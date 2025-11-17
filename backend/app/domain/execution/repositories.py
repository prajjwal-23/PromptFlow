"""
Repository Interfaces for Execution Domain

This module defines abstract repository interfaces following Domain-Driven Design
principles. All repositories are designed for dependency inversion and testability.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID

from .models import Execution, ExecutionEvent, NodeOutput, ExecutionStatus, NodeStatus


class ExecutionRepository(ABC):
    """Repository interface for Execution aggregate."""
    
    @abstractmethod
    async def get_by_id(self, execution_id: str) -> Optional[Execution]:
        """Retrieve an execution by its ID."""
        pass
    
    @abstractmethod
    async def save(self, execution: Execution) -> Execution:
        """Save an execution entity."""
        pass
    
    @abstractmethod
    async def delete(self, execution_id: str) -> bool:
        """Delete an execution by its ID."""
        pass
    
    @abstractmethod
    async def find_by_agent_id(self, agent_id: str) -> List[Execution]:
        """Find all executions for a specific agent."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: ExecutionStatus) -> List[Execution]:
        """Find all executions with a specific status."""
        pass
    
    @abstractmethod
    async def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Execution]:
        """Find executions within a date range."""
        pass
    
    @abstractmethod
    async def find_active_executions(self) -> List[Execution]:
        """Find all currently running executions."""
        pass
    
    @abstractmethod
    async def get_execution_count(self) -> int:
        """Get total count of executions."""
        pass
    
    @abstractmethod
    async def get_metrics_summary(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get execution metrics summary."""
        pass


class EventRepository(ABC):
    """Repository interface for Event storage."""
    
    @abstractmethod
    async def save_event(self, event: ExecutionEvent) -> ExecutionEvent:
        """Save an execution event."""
        pass
    
    @abstractmethod
    async def get_events_by_execution_id(
        self, 
        execution_id: str,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get all events for a specific execution."""
        pass
    
    @abstractmethod
    async def get_events_by_type(
        self, 
        event_type: str,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get events by type."""
        pass
    
    @abstractmethod
    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get events within a date range."""
        pass
    
    @abstractmethod
    async def delete_old_events(
        self, 
        cutoff_date: datetime
    ) -> int:
        """Delete events older than cutoff date. Returns count of deleted events."""
        pass
    
    @abstractmethod
    async def get_event_count(self) -> int:
        """Get total count of events."""
        pass


class NodeOutputRepository(ABC):
    """Repository interface for Node Output storage."""
    
    @abstractmethod
    async def save_output(self, output: NodeOutput) -> NodeOutput:
        """Save a node output."""
        pass
    
    @abstractmethod
    async def get_output(self, execution_id: str, node_id: str) -> Optional[NodeOutput]:
        """Get a specific node output."""
        pass
    
    @abstractmethod
    async def get_outputs_by_execution_id(
        self, 
        execution_id: str
    ) -> List[NodeOutput]:
        """Get all outputs for an execution."""
        pass
    
    @abstractmethod
    async def get_outputs_by_status(
        self, 
        status: NodeStatus,
        limit: Optional[int] = None
    ) -> List[NodeOutput]:
        """Get outputs by status."""
        pass
    
    @abstractmethod
    async def delete_outputs_by_execution_id(self, execution_id: str) -> int:
        """Delete all outputs for an execution. Returns count of deleted outputs."""
        pass
    
    @abstractmethod
    async def get_output_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get output statistics."""
        pass


class CacheRepository(ABC):
    """Repository interface for caching layer."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class LockRepository(ABC):
    """Repository interface for distributed locking."""
    
    @abstractmethod
    async def acquire_lock(
        self, 
        lock_key: str, 
        ttl: int = 30
    ) -> Optional[str]:
        """Acquire a distributed lock. Returns lock token if successful."""
        pass
    
    @abstractmethod
    async def release_lock(self, lock_key: str, lock_token: str) -> bool:
        """Release a distributed lock. Returns True if successful."""
        pass
    
    @abstractmethod
    async def extend_lock(self, lock_key: str, lock_token: str, ttl: int) -> bool:
        """Extend a lock's TTL. Returns True if successful."""
        pass
    
    @abstractmethod
    async def is_locked(self, lock_key: str) -> bool:
        """Check if a lock is currently held."""
        pass


class MetricsRepository(ABC):
    """Repository interface for metrics storage."""
    
    @abstractmethod
    async def record_metric(
        self, 
        metric_name: str, 
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record a metric value."""
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics within a time range."""
        pass
    
    @abstractmethod
    async def get_aggregated_metrics(
        self,
        metric_name: str,
        aggregation: str,  # avg, sum, min, max, count
        start_time: datetime,
        end_time: datetime,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Union[int, float]]:
        """Get aggregated metrics."""
        pass
    
    @abstractmethod
    async def delete_old_metrics(
        self, 
        cutoff_date: datetime
    ) -> int:
        """Delete metrics older than cutoff date. Returns count of deleted metrics."""
        pass


# Query interfaces for complex queries
class ExecutionQuery(ABC):
    """Interface for complex execution queries."""
    
    @abstractmethod
    async def find_executions_with_filters(
        self,
        agent_ids: Optional[List[str]] = None,
        statuses: Optional[List[ExecutionStatus]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Execution]:
        """Find executions with multiple filters."""
        pass
    
    @abstractmethod
    async def search_executions(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Execution]:
        """Search executions by text query."""
        pass
    
    @abstractmethod
    async def get_execution_analytics(
        self,
        group_by: str,  # agent_id, status, date, etc.
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get execution analytics grouped by specified field."""
        pass


class EventQuery(ABC):
    """Interface for complex event queries."""
    
    @abstractmethod
    async def find_events_with_filters(
        self,
        execution_ids: Optional[List[str]] = None,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Find events with multiple filters."""
        pass
    
    @abstractmethod
    async def get_event_timeline(
        self,
        execution_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get timeline of events for an execution."""
        pass
    
    @abstractmethod
    async def get_error_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get error events within date range."""
        pass


# Factory interfaces for repository creation
class RepositoryFactory(ABC):
    """Factory interface for creating repository instances."""
    
    @abstractmethod
    def create_execution_repository(self) -> ExecutionRepository:
        """Create execution repository instance."""
        pass
    
    @abstractmethod
    def create_event_repository(self) -> EventRepository:
        """Create event repository instance."""
        pass
    
    @abstractmethod
    def create_node_output_repository(self) -> NodeOutputRepository:
        """Create node output repository instance."""
        pass
    
    @abstractmethod
    def create_cache_repository(self) -> CacheRepository:
        """Create cache repository instance."""
        pass
    
    @abstractmethod
    def create_lock_repository(self) -> LockRepository:
        """Create lock repository instance."""
        pass
    
    @abstractmethod
    def create_metrics_repository(self) -> MetricsRepository:
        """Create metrics repository instance."""
        pass


# Unit of Work interface for transaction management
class UnitOfWork(ABC):
    """Unit of Work interface for transaction management."""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter unit of work context."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit unit of work context."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction."""
        pass
    
    @abstractmethod
    def get_execution_repository(self) -> ExecutionRepository:
        """Get execution repository."""
        pass
    
    @abstractmethod
    def get_event_repository(self) -> EventRepository:
        """Get event repository."""
        pass
    
    @abstractmethod
    def get_node_output_repository(self) -> NodeOutputRepository:
        """Get node output repository."""
        pass


# Configuration interfaces
class RepositoryConfig(ABC):
    """Configuration interface for repositories."""
    
    @abstractmethod
    def get_connection_string(self) -> str:
        """Get database connection string."""
        pass
    
    @abstractmethod
    def get_pool_size(self) -> int:
        """Get connection pool size."""
        pass
    
    @abstractmethod
    def get_timeout(self) -> int:
        """Get operation timeout in seconds."""
        pass
    
    @abstractmethod
    def get_retry_count(self) -> int:
        """Get retry count for operations."""
        pass
    
    @abstractmethod
    def get_retry_delay(self) -> float:
        """Get retry delay in seconds."""
        pass


# Health check interface
class HealthCheckRepository(ABC):
    """Repository interface for health checks."""
    
    @abstractmethod
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        pass
    
    @abstractmethod
    async def check_cache_health(self) -> Dict[str, Any]:
        """Check cache health."""
        pass
    
    @abstractmethod
    async def check_lock_health(self) -> Dict[str, Any]:
        """Check distributed lock health."""
        pass
    
    @abstractmethod
    async def check_metrics_health(self) -> Dict[str, Any]:
        """Check metrics storage health."""
        pass