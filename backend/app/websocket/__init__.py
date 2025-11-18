"""
WebSocket Module

This module provides the complete WebSocket infrastructure for the PromptFlow execution engine
with enterprise-grade patterns including connection management, event streaming, and real-time updates.
"""

from .manager import (
    WebSocketManager,
    WebSocketConfig,
    WebSocketMessage,
    WebSocketConnection,
    WebSocketStatus,
    MessageType,
    WebSocketMetrics,
    DeadLetterQueue,
    websocket_manager,
)

# Export get_websocket_manager for external access
def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager

from .streaming import (
    EventStreamer,
    StreamFilter,
    StreamEventType,
    StreamSubscription,
    EventCache,
    initialize_event_streamer,
    get_event_streamer,
)

from .api import router as websocket_router
from .client import (
    WebSocketClient,
    PromptFlowWebSocketClient,
    create_websocket_client,
    create_promptflow_client,
)

# Export all WebSocket components
__all__ = [
    # WebSocket Manager
    "WebSocketManager",
    "WebSocketConfig",
    "WebSocketMessage",
    "WebSocketConnection",
    "WebSocketStatus",
    "MessageType",
    "WebSocketMetrics",
    "DeadLetterQueue",
    "websocket_manager",
    
    # Event Streaming
    "EventStreamer",
    "StreamFilter",
    "StreamEventType",
    "StreamSubscription",
    "EventCache",
    "initialize_event_streamer",
    "get_event_streamer",
    
    # WebSocket API
    "websocket_router",
    
    # WebSocket Client
    "WebSocketClient",
    "PromptFlowWebSocketClient",
    "create_websocket_client",
    "create_promptflow_client",
]

# Version info
__version__ = "1.0.0"