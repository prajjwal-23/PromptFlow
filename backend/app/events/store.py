"""
Event Store Implementation

This module provides the event store for persisting and retrieving events
with enterprise-grade patterns including event sourcing, snapshots, and
performance optimization.
"""

from __future__ import annotations
import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
import threading
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import timedelta

from ..domain.execution.models import ExecutionEvent, EventType, DomainEvent
from ..core.database import get_db
from ..core.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(str, Enum):
    """Event storage backend types."""
    MEMORY = "memory"
    DATABASE = "database"
    FILE = "file"
    REDIS = "redis"


@dataclass
class EventStoreConfig:
    """Configuration for event store."""
    backend: StorageBackend = StorageBackend.MEMORY
    max_events_in_memory: int = 10000
    enable_snapshots: bool = True
    snapshot_interval: int = 100  # events per snapshot
    enable_compression: bool = True
    file_path: Optional[str] = None
    redis_url: Optional[str] = None
    retention_days: int = 30
    enable_indexes: bool = True
    batch_size: int = 100
    flush_interval: float = 1.0  # seconds


@dataclass
class StoredEvent:
    """Event as stored in the event store."""
    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    event_data: Dict[str, Any]
    metadata: Dict[str, Any]
    sequence_number: int
    timestamp: datetime
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "event_data": self.event_data,
            "metadata": self.metadata,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StoredEvent:
        """Create from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            event_data=data["event_data"],
            metadata=data["metadata"],
            sequence_number=data["sequence_number"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            version=data.get("version", 1),
        )


@dataclass
class EventStream:
    """Stream of events for an aggregate."""
    aggregate_id: str
    aggregate_type: str
    events: List[StoredEvent] = field(default_factory=list)
    current_version: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_event(self, event: StoredEvent) -> None:
        """Add event to stream."""
        self.events.append(event)
        self.current_version = event.sequence_number
        self.last_updated = event.timestamp
    
    def get_events_since(self, version: int) -> List[StoredEvent]:
        """Get events since specific version."""
        return [e for e in self.events if e.sequence_number > version]


@dataclass
class Snapshot:
    """Snapshot of aggregate state."""
    aggregate_id: str
    aggregate_type: str
    data: Dict[str, Any]
    version: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "data": self.data,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Snapshot:
        """Create from dictionary."""
        return cls(
            aggregate_id=data["aggregate_id"],
            aggregate_type=data["aggregate_type"],
            data=data["data"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class MemoryEventStore:
    """In-memory event store implementation."""
    
    def __init__(self, config: EventStoreConfig):
        """Initialize memory event store."""
        self._config = config
        self._streams: Dict[str, EventStream] = {}
        self._snapshots: Dict[str, Snapshot] = {}
        self._events_by_type: Dict[EventType, List[StoredEvent]] = defaultdict(list)
        self._sequence_numbers: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
        self._metrics = {
            "events_stored": 0,
            "snapshots_created": 0,
            "queries_executed": 0,
            "storage_size": 0,
        }
    
    async def store_event(self, event: ExecutionEvent, aggregate_type: str = "execution") -> None:
        """Store an event."""
        with self._lock:
            # Get next sequence number
            sequence_number = self._sequence_numbers[event.execution_id] + 1
            self._sequence_numbers[event.execution_id] = sequence_number
            
            # Create stored event
            stored_event = StoredEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.execution_id,
                aggregate_type=aggregate_type,
                event_data=event.data,
                metadata=event.metadata,
                sequence_number=sequence_number,
                timestamp=event.timestamp,
            )
            
            # Get or create stream
            stream = self._streams.get(event.execution_id)
            if stream is None:
                stream = EventStream(
                    aggregate_id=event.execution_id,
                    aggregate_type=aggregate_type
                )
                self._streams[event.execution_id] = stream
            
            # Add event to stream
            stream.add_event(stored_event)
            
            # Add to type index
            self._events_by_type[event.event_type].append(stored_event)
            
            # Update metrics
            self._metrics["events_stored"] += 1
            self._metrics["storage_size"] = self._estimate_storage_size()
            
            # Create snapshot if needed
            if (self._config.enable_snapshots and 
                sequence_number % self._config.snapshot_interval == 0):
                await self._create_snapshot(event.execution_id, aggregate_type)
            
            # Cleanup old events if needed
            await self._cleanup_old_events()
    
    async def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[StoredEvent]:
        """Get events for an aggregate."""
        with self._lock:
            self._metrics["queries_executed"] += 1
            
            stream = self._streams.get(aggregate_id)
            if not stream:
                return []
            
            events = stream.events
            
            # Apply version filters
            if from_version is not None:
                events = [e for e in events if e.sequence_number >= from_version]
            if to_version is not None:
                events = [e for e in events if e.sequence_number <= to_version]
            
            return events
    
    async def get_events_by_type(
        self,
        event_type: EventType,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[StoredEvent]:
        """Get events by type."""
        with self._lock:
            self._metrics["queries_executed"] += 1
            
            events = self._events_by_type.get(event_type, [])
            
            # Apply time filters
            if from_timestamp is not None:
                events = [e for e in events if e.timestamp >= from_timestamp]
            if to_timestamp is not None:
                events = [e for e in events if e.timestamp <= to_timestamp]
            
            return events
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get latest snapshot for an aggregate."""
        with self._lock:
            return self._snapshots.get(aggregate_id)
    
    async def create_snapshot(self, aggregate_id: str, data: Dict[str, Any]) -> None:
        """Create a snapshot."""
        with self._lock:
            stream = self._streams.get(aggregate_id)
            if not stream:
                return
            
            snapshot = Snapshot(
                aggregate_id=aggregate_id,
                aggregate_type=stream.aggregate_type,
                data=data,
                version=stream.current_version,
            )
            
            self._snapshots[aggregate_id] = snapshot
            self._metrics["snapshots_created"] += 1
    
    async def _create_snapshot(self, aggregate_id: str, aggregate_type: str) -> None:
        """Internal snapshot creation."""
        # This would typically reconstruct the aggregate state
        # For now, we'll create a simple snapshot
        stream = self._streams.get(aggregate_id)
        if not stream:
            return
        
        snapshot_data = {
            "current_version": stream.current_version,
            "event_count": len(stream.events),
            "last_updated": stream.last_updated.isoformat(),
        }
        
        await self.create_snapshot(aggregate_id, snapshot_data)
    
    async def _cleanup_old_events(self) -> None:
        """Cleanup old events based on retention policy."""
        if self._config.retention_days <= 0:
            return
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self._config.retention_days)
        
        with self._lock:
            for stream in self._streams.values():
                # Remove old events
                old_events = [e for e in stream.events if e.timestamp < cutoff_time]
                for event in old_events:
                    stream.events.remove(event)
                    # Remove from type index
                    if event in self._events_by_type[event.event_type]:
                        self._events_by_type[event.event_type].remove(event)
    
    def _estimate_storage_size(self) -> int:
        """Estimate storage size in bytes."""
        size = 0
        for stream in self._streams.values():
            for event in stream.events:
                size += len(json.dumps(event.to_dict()).encode('utf-8'))
        return size
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get event store metrics."""
        with self._lock:
            return {
                **self._metrics,
                "stream_count": len(self._streams),
                "snapshot_count": len(self._snapshots),
                "event_types": list(self._events_by_type.keys()),
            }


class DatabaseEventStore:
    """Database-backed event store implementation."""
    
    def __init__(self, config: EventStoreConfig):
        """Initialize database event store."""
        self._config = config
        self._logger = get_logger(f"{__name__}.DatabaseEventStore")
    
    async def store_event(self, event: ExecutionEvent, aggregate_type: str = "execution") -> None:
        """Store an event in database."""
        # This would implement actual database storage
        # For now, we'll log the event
        self._logger.info(f"Storing event {event.event_id} for execution {event.execution_id}")
    
    async def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[StoredEvent]:
        """Get events from database."""
        # This would implement actual database retrieval
        return []
    
    async def get_events_by_type(
        self,
        event_type: EventType,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[StoredEvent]:
        """Get events by type from database."""
        # This would implement actual database retrieval
        return []
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get snapshot from database."""
        # This would implement actual database retrieval
        return None
    
    async def create_snapshot(self, aggregate_id: str, data: Dict[str, Any]) -> None:
        """Create snapshot in database."""
        # This would implement actual database storage
        pass


class EventStore:
    """Main event store interface with backend selection."""
    
    def __init__(self, config: EventStoreConfig):
        """Initialize event store."""
        self._config = config
        self._backend = self._create_backend()
        self._logger = get_logger(__name__)
    
    def _create_backend(self) -> Union[MemoryEventStore, DatabaseEventStore]:
        """Create appropriate backend based on configuration."""
        if self._config.backend == StorageBackend.MEMORY:
            return MemoryEventStore(self._config)
        elif self._config.backend == StorageBackend.DATABASE:
            return DatabaseEventStore(self._config)
        else:
            raise ValueError(f"Unsupported backend: {self._config.backend}")
    
    async def store_event(self, event: ExecutionEvent, aggregate_type: str = "execution") -> None:
        """Store an event."""
        try:
            await self._backend.store_event(event, aggregate_type)
            self._logger.debug(f"Stored event {event.event_id}")
        except Exception as e:
            self._logger.error(f"Failed to store event {event.event_id}: {e}")
            raise
    
    async def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None
    ) -> List[StoredEvent]:
        """Get events for an aggregate."""
        try:
            return await self._backend.get_events(aggregate_id, from_version, to_version)
        except Exception as e:
            self._logger.error(f"Failed to get events for {aggregate_id}: {e}")
            raise
    
    async def get_events_by_type(
        self,
        event_type: EventType,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[StoredEvent]:
        """Get events by type."""
        try:
            return await self._backend.get_events_by_type(event_type, from_timestamp, to_timestamp)
        except Exception as e:
            self._logger.error(f"Failed to get events by type {event_type}: {e}")
            raise
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get latest snapshot for an aggregate."""
        try:
            return await self._backend.get_snapshot(aggregate_id)
        except Exception as e:
            self._logger.error(f"Failed to get snapshot for {aggregate_id}: {e}")
            raise
    
    async def create_snapshot(self, aggregate_id: str, data: Dict[str, Any]) -> None:
        """Create a snapshot."""
        try:
            await self._backend.create_snapshot(aggregate_id, data)
            self._logger.debug(f"Created snapshot for {aggregate_id}")
        except Exception as e:
            self._logger.error(f"Failed to create snapshot for {aggregate_id}: {e}")
            raise
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get event store metrics."""
        try:
            if hasattr(self._backend, 'get_metrics'):
                return await self._backend.get_metrics()
            return {}
        except Exception as e:
            self._logger.error(f"Failed to get metrics: {e}")
            return {}
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for transactional operations."""
        # This would implement transaction management
        try:
            yield
        except Exception as e:
            self._logger.error(f"Transaction failed: {e}")
            raise


# Global event store instance
_default_event_store: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """Get the default event store instance."""
    global _default_event_store
    if _default_event_store is None:
        config = EventStoreConfig()
        _default_event_store = EventStore(config)
    return _default_event_store


def configure_event_store(config: EventStoreConfig) -> EventStore:
    """Configure and return a new event store instance."""
    return EventStore(config)