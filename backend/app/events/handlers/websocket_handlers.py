"""
WebSocket Event Handlers

This module provides WebSocket event handlers for real-time event streaming
with enterprise-grade patterns including connection management, broadcasting,
and performance optimization.
"""

from __future__ import annotations
import asyncio
import json
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
import weakref

from .execution_handlers import BaseEventHandler, HandlerConfig
from ...domain.execution.models import ExecutionEvent, EventType
from ...core.logging import get_logger

logger = get_logger(__name__)


class ConnectionStatus(str, Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketConnection:
    """WebSocket connection information."""
    connection_id: str
    websocket: Any  # WebSocket object
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    node_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    status: ConnectionStatus = ConnectionStatus.CONNECTING
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
    
    def is_subscribed(self, event_type: str) -> bool:
        """Check if connection is subscribed to event type."""
        return event_type in self.subscriptions or "*" in self.subscriptions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "execution_id": self.execution_id,
            "node_id": self.node_id,
            "subscriptions": list(self.subscriptions),
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket handlers."""
    max_connections: int = 1000
    connection_timeout: int = 300  # seconds
    heartbeat_interval: int = 30  # seconds
    max_message_size: int = 1024 * 1024  # 1MB
    enable_compression: bool = True
    buffer_size: int = 1000
    broadcast_batch_size: int = 100
    enable_metrics: bool = True


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self, config: WebSocketConfig):
        """Initialize WebSocket manager."""
        self._config = config
        self._connections: Dict[str, WebSocketConnection] = {}
        self._execution_subscribers: Dict[str, Set[str]] = {}  # execution_id -> connection_ids
        self._node_subscribers: Dict[str, Set[str]] = {}  # node_id -> connection_ids
        self._event_subscribers: Dict[str, Set[str]] = {}  # event_type -> connection_ids
        self._lock = asyncio.Lock()
        self._logger = get_logger(f"{__name__}.WebSocketManager")
        self._metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "broadcasts_sent": 0,
        }
    
    async def add_connection(
        self,
        websocket: Any,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        node_id: Optional[str] = None,
        subscriptions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new WebSocket connection."""
        async with self._lock:
            # Check connection limit
            if len(self._connections) >= self._config.max_connections:
                raise RuntimeError("Maximum connections reached")
            
            connection_id = str(uuid.uuid4())
            
            connection = WebSocketConnection(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                execution_id=execution_id,
                node_id=node_id,
                subscriptions=set(subscriptions or []),
                metadata=metadata or {}
            )
            
            self._connections[connection_id] = connection
            
            # Update subscriber indexes
            if execution_id:
                if execution_id not in self._execution_subscribers:
                    self._execution_subscribers[execution_id] = set()
                self._execution_subscribers[execution_id].add(connection_id)
            
            if node_id:
                if node_id not in self._node_subscribers:
                    self._node_subscribers[node_id] = set()
                self._node_subscribers[node_id].add(connection_id)
            
            for event_type in connection.subscriptions:
                if event_type not in self._event_subscribers:
                    self._event_subscribers[event_type] = set()
                self._event_subscribers[event_type].add(connection_id)
            
            # Update metrics
            self._metrics["total_connections"] += 1
            self._metrics["active_connections"] = len(self._connections)
            
            self._logger.info(f"WebSocket connection {connection_id} added")
            
            # Start heartbeat task
            asyncio.create_task(self._heartbeat_loop(connection_id))
            
            return connection_id
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return
            
            # Remove from subscriber indexes
            if connection.execution_id and connection.execution_id in self._execution_subscribers:
                self._execution_subscribers[connection.execution_id].discard(connection_id)
                if not self._execution_subscribers[connection.execution_id]:
                    del self._execution_subscribers[connection.execution_id]
            
            if connection.node_id and connection.node_id in self._node_subscribers:
                self._node_subscribers[connection.node_id].discard(connection_id)
                if not self._node_subscribers[connection.node_id]:
                    del self._node_subscribers[connection.node_id]
            
            for event_type in connection.subscriptions:
                if event_type in self._event_subscribers:
                    self._event_subscribers[event_type].discard(connection_id)
                    if not self._event_subscribers[event_type]:
                        del self._event_subscribers[event_type]
            
            # Remove connection
            del self._connections[connection_id]
            
            # Update metrics
            self._metrics["active_connections"] = len(self._connections)
            
            self._logger.info(f"WebSocket connection {connection_id} removed")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific connection."""
        connection = self._connections.get(connection_id)
        if not connection or connection.status != ConnectionStatus.CONNECTED:
            return False
        
        try:
            # Convert message to JSON
            message_json = json.dumps(message)
            
            # Check message size
            if len(message_json) > self._config.max_message_size:
                self._logger.warning(f"Message too large for connection {connection_id}")
                return False
            
            # Send message
            await connection.websocket.send_text(message_json)
            
            connection.update_activity()
            self._metrics["messages_sent"] += 1
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to send message to connection {connection_id}: {e}")
            self._metrics["messages_failed"] += 1
            
            # Mark connection as error
            connection.status = ConnectionStatus.ERROR
            return False
    
    async def broadcast_to_subscribers(
        self,
        event: ExecutionEvent,
        target_subscribers: Optional[Set[str]] = None
    ) -> int:
        """Broadcast event to subscribed connections."""
        if target_subscribers is None:
            target_subscribers = self._get_subscribers_for_event(event)
        
        if not target_subscribers:
            return 0
        
        # Prepare message
        message = {
            "type": "event",
            "event": event.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Send to all subscribers
        successful_sends = 0
        tasks = []
        
        for connection_id in target_subscribers:
            if connection_id in self._connections:
                tasks.append(self.send_to_connection(connection_id, message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_sends = sum(1 for result in results if result is True)
        
        self._metrics["broadcasts_sent"] += 1
        self._logger.debug(f"Broadcasted event {event.event_id} to {successful_sends} connections")
        
        return successful_sends
    
    def _get_subscribers_for_event(self, event: ExecutionEvent) -> Set[str]:
        """Get connections subscribed to this event."""
        subscribers = set()
        
        # Event type subscribers
        event_type_subscribers = self._event_subscribers.get(event.event_type.value, set())
        subscribers.update(event_type_subscribers)
        
        # Wildcard subscribers
        wildcard_subscribers = self._event_subscribers.get("*", set())
        subscribers.update(wildcard_subscribers)
        
        # Execution-specific subscribers
        if event.execution_id:
            execution_subscribers = self._execution_subscribers.get(event.execution_id, set())
            subscribers.update(execution_subscribers)
        
        # Node-specific subscribers
        if event.node_id:
            node_subscribers = self._node_subscribers.get(event.node_id, set())
            subscribers.update(node_subscribers)
        
        return subscribers
    
    async def _heartbeat_loop(self, connection_id: str) -> None:
        """Heartbeat loop for connection."""
        while True:
            try:
                await asyncio.sleep(self._config.heartbeat_interval)
                
                connection = self._connections.get(connection_id)
                if not connection:
                    break
                
                # Check timeout
                now = datetime.now(timezone.utc)
                if (now - connection.last_activity).total_seconds() > self._config.connection_timeout:
                    self._logger.info(f"Connection {connection_id} timed out")
                    await self.remove_connection(connection_id)
                    break
                
                # Send heartbeat
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": now.isoformat(),
                }
                
                if not await self.send_to_connection(connection_id, heartbeat_message):
                    self._logger.warning(f"Heartbeat failed for connection {connection_id}")
                    await self.remove_connection(connection_id)
                    break
                
            except Exception as e:
                self._logger.error(f"Heartbeat error for connection {connection_id}: {e}")
                break
    
    async def cleanup_stale_connections(self) -> int:
        """Clean up stale connections."""
        now = datetime.now(timezone.utc)
        stale_connections = []
        
        for connection_id, connection in self._connections.items():
            if (now - connection.last_activity).total_seconds() > self._config.connection_timeout:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            await self.remove_connection(connection_id)
        
        return len(stale_connections)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get WebSocket manager metrics."""
        return {
            **self._metrics,
            "execution_subscribers": len(self._execution_subscribers),
            "node_subscribers": len(self._node_subscribers),
            "event_subscribers": len(self._event_subscribers),
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information."""
        connection = self._connections.get(connection_id)
        return connection.to_dict() if connection else None


class WebSocketEventHandler(BaseEventHandler):
    """WebSocket event handler for real-time event streaming."""
    
    def __init__(self, config: HandlerConfig, ws_config: WebSocketConfig):
        """Initialize WebSocket event handler."""
        super().__init__(config)
        self._ws_manager = WebSocketManager(ws_config)
        self._logger = get_logger(f"{__name__}.WebSocketEventHandler")
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle event by broadcasting to WebSocket subscribers."""
        try:
            # Broadcast to subscribers
            await self._ws_manager.broadcast_to_subscribers(event)
            
        except Exception as e:
            self._logger.error(f"WebSocket handler error: {e}")
            raise
    
    async def add_connection(
        self,
        websocket: Any,
        user_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        node_id: Optional[str] = None,
        subscriptions: Optional[List[str]] = None
    ) -> str:
        """Add WebSocket connection."""
        return await self._ws_manager.add_connection(
            websocket, user_id, execution_id, node_id, subscriptions
        )
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove WebSocket connection."""
        await self._ws_manager.remove_connection(connection_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get handler metrics."""
        return {
            **super().get_metrics(),
            "websocket": self._ws_manager.get_metrics(),
        }


class StreamingEventHandler(BaseEventHandler):
    """Handler for streaming events to clients."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize streaming event handler."""
        super().__init__(config)
        self._active_streams: Dict[str, asyncio.Queue] = {}
        self._stream_subscriptions: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._logger = get_logger(f"{__name__}.StreamingEventHandler")
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle streaming event."""
        async with self._lock:
            # Find relevant streams
            stream_ids = self._get_stream_ids_for_event(event)
            
            for stream_id in stream_ids:
                if stream_id in self._active_streams:
                    try:
                        await self._active_streams[stream_id].put(event)
                    except Exception as e:
                        self._logger.error(f"Failed to add event to stream {stream_id}: {e}")
    
    def _get_stream_ids_for_event(self, event: ExecutionEvent) -> Set[str]:
        """Get stream IDs that should receive this event."""
        stream_ids = set()
        
        # Execution-specific streams
        execution_streams = self._stream_subscriptions.get(f"execution:{event.execution_id}", set())
        stream_ids.update(execution_streams)
        
        # Node-specific streams
        if event.node_id:
            node_streams = self._stream_subscriptions.get(f"node:{event.node_id}", set())
            stream_ids.update(node_streams)
        
        # Event type streams
        event_streams = self._stream_subscriptions.get(f"event:{event.event_type.value}", set())
        stream_ids.update(event_streams)
        
        # Global streams
        global_streams = self._stream_subscriptions.get("global", set())
        stream_ids.update(global_streams)
        
        return stream_ids
    
    async def create_stream(
        self,
        stream_id: str,
        subscriptions: List[str],
        buffer_size: int = 100
    ) -> asyncio.Queue:
        """Create a new event stream."""
        async with self._lock:
            if stream_id in self._active_streams:
                raise ValueError(f"Stream {stream_id} already exists")
            
            queue = asyncio.Queue(maxsize=buffer_size)
            self._active_streams[stream_id] = queue
            
            # Register subscriptions
            for subscription in subscriptions:
                if subscription not in self._stream_subscriptions:
                    self._stream_subscriptions[subscription] = set()
                self._stream_subscriptions[subscription].add(stream_id)
            
            self._logger.info(f"Created stream {stream_id} with subscriptions: {subscriptions}")
            
            return queue
    
    async def close_stream(self, stream_id: str) -> None:
        """Close an event stream."""
        async with self._lock:
            if stream_id not in self._active_streams:
                return
            
            # Remove queue
            del self._active_streams[stream_id]
            
            # Remove subscriptions
            for subscription, stream_ids in self._stream_subscriptions.items():
                stream_ids.discard(stream_id)
                if not stream_ids:
                    del self._stream_subscriptions[subscription]
            
            self._logger.info(f"Closed stream {stream_id}")
    
    async def get_stream_events(self, stream_id: str) -> AsyncGenerator[ExecutionEvent, None]:
        """Get events from a stream."""
        if stream_id not in self._active_streams:
            raise ValueError(f"Stream {stream_id} does not exist")
        
        queue = self._active_streams[stream_id]
        
        while True:
            try:
                event = await queue.get()
                yield event
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error getting event from stream {stream_id}: {e}")
                break


# Factory function for creating WebSocket handlers
def create_websocket_handlers(
    handler_config: HandlerConfig,
    ws_config: WebSocketConfig
) -> List[BaseEventHandler]:
    """Create WebSocket event handlers."""
    return [
        WebSocketEventHandler(handler_config, ws_config),
        StreamingEventHandler(handler_config),
    ]