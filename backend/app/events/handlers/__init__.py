"""
Event Handlers Module

This module provides event handlers for processing execution events
with enterprise-grade patterns including async processing, error handling,
and performance monitoring.
"""

from .execution_handlers import (
    ExecutionEventHandler,
    NodeEventHandler,
    MetricsEventHandler,
    NotificationEventHandler,
)

from .websocket_handlers import (
    WebSocketEventHandler,
    StreamingEventHandler,
)

from .persistence_handlers import (
    PersistenceEventHandler,
    CacheEventHandler,
)

__all__ = [
    # Execution handlers
    "ExecutionEventHandler",
    "NodeEventHandler", 
    "MetricsEventHandler",
    "NotificationEventHandler",
    
    # WebSocket handlers
    "WebSocketEventHandler",
    "StreamingEventHandler",
    
    # Persistence handlers
    "PersistenceEventHandler",
    "CacheEventHandler",
]

__version__ = "1.0.0"