"""
Events Module

This module provides the complete event system for the PromptFlow execution engine
including event bus, event store, and event handlers with enterprise-grade patterns.
"""

from .bus import (
    EventBus,
    EventBusConfig,
    get_event_bus,
    configure_event_bus,
)

from .store import (
    EventStore,
    EventStoreConfig,
    StoredEvent,
    EventStream,
    Snapshot,
    StorageBackend,
    MemoryEventStore,
    DatabaseEventStore,
    get_event_store,
    configure_event_store,
)

from .handlers import (
    # Execution handlers
    ExecutionEventHandler,
    NodeEventHandler,
    MetricsEventHandler,
    NotificationEventHandler,
    
    # WebSocket handlers
    WebSocketEventHandler,
    StreamingEventHandler,
    
    # Persistence handlers
    PersistenceEventHandler,
    CacheEventHandler,
)

# Export all event system components
__all__ = [
    # Event Bus
    "EventBus",
    "EventBusConfig",
    "get_event_bus",
    "configure_event_bus",
    
    # Event Store
    "EventStore",
    "EventStoreConfig",
    "StoredEvent",
    "EventStream",
    "Snapshot",
    "StorageBackend",
    "MemoryEventStore",
    "DatabaseEventStore",
    "get_event_store",
    "configure_event_store",
    
    # Execution Handlers
    "ExecutionEventHandler",
    "NodeEventHandler",
    "MetricsEventHandler",
    "NotificationEventHandler",
    
    # WebSocket Handlers
    "WebSocketEventHandler",
    "StreamingEventHandler",
    
    # Persistence Handlers
    "PersistenceEventHandler",
    "CacheEventHandler",
]

# Version info
__version__ = "1.0.0"