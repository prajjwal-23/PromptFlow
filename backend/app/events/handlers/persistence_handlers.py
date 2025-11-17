"""
Persistence Event Handlers

This module provides persistence event handlers for storing events
with enterprise-grade patterns including database operations, caching,
and performance optimization.
"""

from __future__ import annotations
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import uuid

from .execution_handlers import BaseEventHandler, HandlerConfig
from ...domain.execution.models import ExecutionEvent, EventType
from ...core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PersistenceConfig:
    """Configuration for persistence handlers."""
    enable_database: bool = True
    enable_cache: bool = True
    cache_ttl: int = 3600  # seconds
    batch_size: int = 100
    flush_interval: float = 5.0  # seconds
    enable_compression: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0


class DatabasePersistenceHandler(BaseEventHandler):
    """Handler for persisting events to database."""
    
    def __init__(self, config: HandlerConfig, persistence_config: PersistenceConfig):
        """Initialize database persistence handler."""
        super().__init__(config)
        self._persistence_config = persistence_config
        self._pending_events: List[ExecutionEvent] = []
        self._flush_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._logger = get_logger(f"{__name__}.DatabasePersistenceHandler")
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle event by adding to pending batch."""
        if not self._persistence_config.enable_database:
            return
        
        async with self._lock:
            self._pending_events.append(event)
            
            # Start flush task if not running
            if self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._flush_loop())
            
            # Flush immediately if batch size reached
            if len(self._pending_events) >= self._persistence_config.batch_size:
                await self._flush_events()
    
    async def _flush_loop(self) -> None:
        """Background loop for periodic flushing."""
        while True:
            try:
                await asyncio.sleep(self._persistence_config.flush_interval)
                await self._flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Flush loop error: {e}")
    
    async def _flush_events(self) -> None:
        """Flush pending events to database."""
        if not self._pending_events:
            return
        
        events_to_flush = self._pending_events.copy()
        self._pending_events.clear()
        
        if not events_to_flush:
            return
        
        try:
            await self._persist_events(events_to_flush)
            self._logger.debug(f"Flushed {len(events_to_flush)} events to database")
        except Exception as e:
            self._logger.error(f"Failed to flush events to database: {e}")
            # Re-add events to pending for retry
            self._pending_events.extend(events_to_flush)
    
    async def _persist_events(self, events: List[ExecutionEvent]) -> None:
        """Persist events to database with retry logic."""
        for attempt in range(self._persistence_config.retry_attempts + 1):
            try:
                # This would implement actual database persistence
                # For now, we'll simulate the operation
                await self._simulate_database_write(events)
                return
                
            except Exception as e:
                self._logger.error(f"Database persistence attempt {attempt + 1} failed: {e}")
                
                if attempt < self._persistence_config.retry_attempts:
                    await asyncio.sleep(self._persistence_config.retry_delay * (2 ** attempt))
                else:
                    raise
    
    async def _simulate_database_write(self, events: List[ExecutionEvent]) -> None:
        """Simulate database write operation."""
        # Simulate database latency
        await asyncio.sleep(0.01)
        
        # Log what would be written
        event_ids = [event.event_id for event in events]
        self._logger.debug(f"Would write events {event_ids} to database")
    
    async def flush_all(self) -> None:
        """Flush all pending events immediately."""
        await self._flush_events()
        
        # Cancel flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass


class CachePersistenceHandler(BaseEventHandler):
    """Handler for caching events in memory."""
    
    def __init__(self, config: HandlerConfig, persistence_config: PersistenceConfig):
        """Initialize cache persistence handler."""
        super().__init__(config)
        self._persistence_config = persistence_config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._execution_cache: Dict[str, List[ExecutionEvent]] = {}
        self._node_cache: Dict[str, List[ExecutionEvent]] = {}
        self._event_type_cache: Dict[str, List[ExecutionEvent]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._logger = get_logger(f"{__name__}.CachePersistenceHandler")
        
        # Start cleanup task
        if self._persistence_config.enable_cache:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle event by caching it."""
        if not self._persistence_config.enable_cache:
            return
        
        async with self._lock:
            # Cache by event ID
            self._cache[event.event_id] = {
                "event": event.to_dict(),
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl": self._persistence_config.cache_ttl,
            }
            
            # Cache by execution ID
            if event.execution_id not in self._execution_cache:
                self._execution_cache[event.execution_id] = []
            self._execution_cache[event.execution_id].append(event)
            
            # Cache by node ID
            if event.node_id:
                if event.node_id not in self._node_cache:
                    self._node_cache[event.node_id] = []
                self._node_cache[event.node_id].append(event)
            
            # Cache by event type
            event_type_key = event.event_type.value
            if event_type_key not in self._event_type_cache:
                self._event_type_cache[event_type_key] = []
            self._event_type_cache[event_type_key].append(event)
            
            self._logger.debug(f"Cached event {event.event_id}")
    
    async def get_event(self, event_id: str) -> Optional[ExecutionEvent]:
        """Get event from cache."""
        async with self._lock:
            cached = self._cache.get(event_id)
            if not cached:
                return None
            
            # Check TTL
            cached_at = datetime.fromisoformat(cached["cached_at"])
            if (datetime.now(timezone.utc) - cached_at).total_seconds() > cached["ttl"]:
                del self._cache[event_id]
                return None
            
            # Reconstruct event
            event_data = cached["event"]
            return ExecutionEvent(
                event_id=event_data["event_id"],
                event_type=EventType(event_data["event_type"]),
                execution_id=event_data["execution_id"],
                node_id=event_data.get("node_id"),
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                data=event_data["data"],
                metadata=event_data["metadata"],
            )
    
    async def get_execution_events(self, execution_id: str) -> List[ExecutionEvent]:
        """Get all events for an execution."""
        async with self._lock:
            events = self._execution_cache.get(execution_id, [])
            return [event for event in events if await self._is_event_valid(event)]
    
    async def get_node_events(self, node_id: str) -> List[ExecutionEvent]:
        """Get all events for a node."""
        async with self._lock:
            events = self._node_cache.get(node_id, [])
            return [event for event in events if await self._is_event_valid(event)]
    
    async def get_events_by_type(self, event_type: EventType) -> List[ExecutionEvent]:
        """Get all events of a specific type."""
        async with self._lock:
            events = self._event_type_cache.get(event_type.value, [])
            return [event for event in events if await self._is_event_valid(event)]
    
    async def _is_event_valid(self, event: ExecutionEvent) -> bool:
        """Check if event is still valid (not expired)."""
        cached = self._cache.get(event.event_id)
        if not cached:
            return False
        
        cached_at = datetime.fromisoformat(cached["cached_at"])
        return (datetime.now(timezone.utc) - cached_at).total_seconds() <= cached["ttl"]
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleaning up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries."""
        async with self._lock:
            now = datetime.now(timezone.utc)
            expired_keys = []
            
            for event_id, cached in self._cache.items():
                cached_at = datetime.fromisoformat(cached["cached_at"])
                if (now - cached_at).total_seconds() > cached["ttl"]:
                    expired_keys.append(event_id)
            
            # Remove expired entries
            for event_id in expired_keys:
                del self._cache[event_id]
            
            # Clean up execution cache
            for execution_id, events in self._execution_cache.items():
                valid_events = [e for e in events if e.event_id not in expired_keys]
                self._execution_cache[execution_id] = valid_events
            
            # Clean up node cache
            for node_id, events in self._node_cache.items():
                valid_events = [e for e in events if e.event_id not in expired_keys]
                self._node_cache[node_id] = valid_events
            
            # Clean up event type cache
            for event_type, events in self._event_type_cache.items():
                valid_events = [e for e in events if e.event_id not in expired_keys]
                self._event_type_cache[event_type] = valid_events
            
            if expired_keys:
                self._logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        return {
            "total_cached_events": len(self._cache),
            "execution_cache_size": len(self._execution_cache),
            "node_cache_size": len(self._node_cache),
            "event_type_cache_size": len(self._event_type_cache),
            "cache_ttl": self._persistence_config.cache_ttl,
        }
    
    async def clear_cache(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._execution_cache.clear()
            self._node_cache.clear()
            self._event_type_cache.clear()
            self._logger.info("Cache cleared")
    
    async def shutdown(self) -> None:
        """Shutdown the cache handler."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class PersistenceEventHandler(BaseEventHandler):
    """Combined persistence handler with database and cache support."""
    
    def __init__(
        self,
        config: HandlerConfig,
        persistence_config: PersistenceConfig
    ):
        """Initialize persistence event handler."""
        super().__init__(config)
        self._persistence_config = persistence_config
        self._db_handler = DatabasePersistenceHandler(config, persistence_config)
        self._cache_handler = CachePersistenceHandler(config, persistence_config)
        self._logger = get_logger(f"{__name__}.PersistenceEventHandler")
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle event by persisting to database and cache."""
        try:
            # Handle in parallel for better performance
            tasks = []
            
            if self._persistence_config.enable_database:
                tasks.append(self._db_handler.handle_with_retry(event))
            
            if self._persistence_config.enable_cache:
                tasks.append(self._cache_handler.handle_with_retry(event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self._logger.error(f"Persistence handler error: {e}")
            raise
    
    async def get_event(self, event_id: str) -> Optional[ExecutionEvent]:
        """Get event from cache or database."""
        # Try cache first
        if self._persistence_config.enable_cache:
            event = await self._cache_handler.get_event(event_id)
            if event:
                return event
        
        # Fallback to database (would implement actual database query)
        return None
    
    async def get_execution_events(self, execution_id: str) -> List[ExecutionEvent]:
        """Get events for execution from cache or database."""
        # Try cache first
        if self._persistence_config.enable_cache:
            events = await self._cache_handler.get_execution_events(execution_id)
            if events:
                return events
        
        # Fallback to database (would implement actual database query)
        return []
    
    async def flush_all(self) -> None:
        """Flush all pending events."""
        await self._db_handler.flush_all()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get combined metrics."""
        return {
            **super().get_metrics(),
            "database": self._db_handler.get_metrics(),
            "cache": self._cache_handler.get_cache_metrics(),
        }
    
    async def shutdown(self) -> None:
        """Shutdown the persistence handler."""
        await self._db_handler.flush_all()
        await self._cache_handler.shutdown()


class CacheEventHandler(BaseEventHandler):
    """Simplified cache event handler for basic caching needs."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize cache event handler."""
        super().__init__(config)
        self._cache: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._logger = get_logger(f"{__name__}.CacheEventHandler")
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle event by caching it."""
        async with self._lock:
            # Simple cache implementation
            cache_key = f"event:{event.event_id}"
            self._cache[cache_key] = {
                "event": event.to_dict(),
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Also cache by execution
            exec_key = f"execution:{event.execution_id}"
            if exec_key not in self._cache:
                self._cache[exec_key] = {"events": []}
            self._cache[exec_key]["events"].append(event.to_dict())
    
    async def get_cached_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get cached event."""
        async with self._lock:
            cache_key = f"event:{event_id}"
            cached = self._cache.get(cache_key)
            return cached["event"] if cached else None
    
    async def get_cached_execution(self, execution_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached execution events."""
        async with self._lock:
            exec_key = f"execution:{execution_id}"
            cached = self._cache.get(exec_key)
            return cached["events"] if cached else None


# Factory function for creating persistence handlers
def create_persistence_handlers(
    handler_config: HandlerConfig,
    persistence_config: PersistenceConfig
) -> List[BaseEventHandler]:
    """Create persistence event handlers."""
    return [
        PersistenceEventHandler(handler_config, persistence_config),
        CacheEventHandler(handler_config),
    ]