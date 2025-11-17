"""
Enterprise WebSocket Manager for PromptFlow.

This module provides enterprise-grade WebSocket connection management with:
- Connection pooling and lifecycle management
- Real-time event streaming
- Authentication and authorization
- Resource management and monitoring
- Dead letter queue for failed messages
- Comprehensive metrics and logging
"""

import asyncio
import json
import logging
import time
import uuid
import weakref
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any, Callable, Dict, List, Optional, Set, Union
)
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.logging import get_logger


class WebSocketStatus(Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class MessageType(Enum):
    """WebSocket message types."""
    HEARTBEAT = "heartbeat"
    EVENT = "event"
    ERROR = "error"
    AUTH = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id
        }


@dataclass
class WebSocketConnection:
    """WebSocket connection information."""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    status: WebSocketStatus = WebSocketStatus.CONNECTING
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if connection is active."""
        return self.status == WebSocketStatus.CONNECTED
    
    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now(timezone.utc)


@dataclass
class WebSocketMetrics:
    """WebSocket connection metrics."""
    active_connections: int = 0
    total_connections: int = 0
    failed_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    errors: int = 0
    peak_connections: int = 0
    average_session_duration: float = 0.0
    total_session_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "active_connections": self.active_connections,
            "total_connections": self.total_connections,
            "failed_connections": self.failed_connections,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "errors": self.errors,
            "peak_connections": self.peak_connections,
            "average_session_duration": self.average_session_duration,
            "total_session_time": self.total_session_time
        }


@dataclass
class WebSocketConfig:
    """WebSocket manager configuration."""
    max_connections: int = 1000
    heartbeat_interval: float = 30.0
    connection_timeout: float = 300.0
    message_size_limit: int = 1024 * 1024  # 1MB
    enable_metrics: bool = True
    enable_logging: bool = True
    enable_tracing: bool = False
    dead_letter_max_size: int = 1000
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 3


class DeadLetterQueue:
    """Dead letter queue for failed WebSocket messages."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._messages: List[tuple] = []
        self._lock = asyncio.Lock()
    
    async def add(self, message: WebSocketMessage, error: str) -> None:
        """Add failed message to dead letter queue."""
        async with self._lock:
            if len(self._messages) >= self.max_size:
                # Remove oldest message
                self._messages.pop(0)
            
            self._messages.append((message, error, datetime.now(timezone.utc)))
    
    async def get_all(self) -> List[tuple]:
        """Get all messages from dead letter queue."""
        async with self._lock:
            return self._messages.copy()
    
    async def clear(self) -> None:
        """Clear dead letter queue."""
        async with self._lock:
            self._messages.clear()
    
    def size(self) -> int:
        """Get current queue size."""
        return len(self._messages)


class WebSocketManager:
    """Enterprise-grade WebSocket connection manager with pooling and real-time streaming."""
    
    def __init__(self, config: Optional[WebSocketConfig] = None):
        """
        Initialize WebSocket manager.
        
        Args:
            config: WebSocket configuration
        """
        self._config = config or WebSocketConfig()
        self._connections: Dict[str, WebSocketConnection] = {}
        self._dead_letter_queue = DeadLetterQueue(self._config.dead_letter_max_size)
        self._lock = asyncio.Lock()
        self._metrics = WebSocketMetrics()
        self._logger = get_logger(f"{__name__}.WebSocketManager")
        
        # Connection registry for tracking
        self._connection_registry: Dict[str, Dict[str, Any]] = weakref.WeakValueDictionary()
        
        # Event handlers
        self._event_handlers: List[Callable] = []
        self._streaming_subscribers: Dict[str, List[Callable]] = {}
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self._logger.info("WebSocket manager background tasks started")
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID for authentication
            workspace_id: Workspace ID for scoping
            metadata: Additional connection metadata
            
        Returns:
            Connection ID
        """
        connection_id = str(uuid.uuid4())
        
        # Check connection limit
        if len(self._connections) >= self._config.max_connections:
            await websocket.close(code=1008, reason="Connection limit exceeded")
            self._metrics.failed_connections += 1
            raise ConnectionError("Maximum connections exceeded")
        
        try:
            # Accept WebSocket connection
            await websocket.accept()
            
            # Create connection object
            connection = WebSocketConnection(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                workspace_id=workspace_id,
                status=WebSocketStatus.CONNECTED,
                metadata=metadata or {}
            )
            
            # Register connection
            async with self._lock:
                self._connections[connection_id] = connection
                self._connection_registry[connection_id] = {
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "connected_at": connection.connected_at
                }
            
            # Update metrics
            self._metrics.total_connections += 1
            self._metrics.active_connections = len(self._connections)
            self._metrics.peak_connections = max(
                self._metrics.peak_connections,
                self._metrics.active_connections
            )
            
            # Send welcome message
            await self._send_to_connection(connection, WebSocketMessage(
                type=MessageType.AUTH,
                data={"status": "connected", "connection_id": connection_id}
            ))
            
            self._logger.info(
                f"WebSocket connected: {connection_id} "
                f"(user: {user_id}, workspace: {workspace_id})"
            )
            
            return connection_id
            
        except Exception as e:
            self._metrics.failed_connections += 1
            self._logger.error(f"Failed to connect WebSocket: {e}")
            raise
    
    async def disconnect(self, connection_id: str, reason: str = "Client disconnect") -> None:
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection ID to disconnect
            reason: Disconnect reason
        """
        async with self._lock:
            if connection_id not in self._connections:
                return
            
            connection = self._connections[connection_id]
            connection.status = WebSocketStatus.DISCONNECTING
            
            try:
                # Calculate session duration
                session_duration = (
                    datetime.now(timezone.utc) - connection.connected_at
                ).total_seconds()
                self._metrics.total_session_time += session_duration
                
                # Close WebSocket
                await connection.websocket.close(code=1000, reason=reason)
                
                # Remove from connections
                del self._connections[connection_id]
                
                # Remove from registry
                if connection_id in self._connection_registry:
                    del self._connection_registry[connection_id]
                
                # Update metrics
                self._metrics.active_connections = len(self._connections)
                
                self._logger.info(f"WebSocket disconnected: {connection_id} ({reason})")
                
            except Exception as e:
                self._logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
                connection.status = WebSocketStatus.ERROR
    
    async def send_message(
        self,
        connection_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: Target connection ID
            message_type: Type of message
            data: Message data
            
        Returns:
            True if message sent successfully
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            if not connection.is_active():
                return False
            
            message = WebSocketMessage(type=message_type, data=data)
            return await self._send_to_connection(connection, message)
    
    async def broadcast_to_workspace(
        self,
        workspace_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast message to all connections in a workspace.
        
        Args:
            workspace_id: Target workspace ID
            message_type: Type of message
            data: Message data
            
        Returns:
            Number of connections message was sent to
        """
        message = WebSocketMessage(type=message_type, data=data)
        sent_count = 0
        
        async with self._lock:
            for connection in self._connections.values():
                if (
                    connection.is_active() and
                    connection.workspace_id == workspace_id
                ):
                    if await self._send_to_connection(connection, message):
                        sent_count += 1
        
        return sent_count
    
    async def broadcast_to_user(
        self,
        user_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast message to all connections for a user.
        
        Args:
            user_id: Target user ID
            message_type: Type of message
            data: Message data
            
        Returns:
            Number of connections message was sent to
        """
        message = WebSocketMessage(type=message_type, data=data)
        sent_count = 0
        
        async with self._lock:
            for connection in self._connections.values():
                if (
                    connection.is_active() and
                    connection.user_id == user_id
                ):
                    if await self._send_to_connection(connection, message):
                        sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(
        self,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast message to all active connections.
        
        Args:
            message_type: Type of message
            data: Message data
            
        Returns:
            Number of connections message was sent to
        """
        message = WebSocketMessage(type=message_type, data=data)
        sent_count = 0
        
        async with self._lock:
            for connection in self._connections.values():
                if connection.is_active():
                    if await self._send_to_connection(connection, message):
                        sent_count += 1
        
        return sent_count
    
    async def subscribe_to_events(
        self,
        connection_id: str,
        event_types: List[str]
    ) -> bool:
        """
        Subscribe connection to specific event types.
        
        Args:
            connection_id: Connection ID
            event_types: List of event types to subscribe to
            
        Returns:
            True if subscription successful
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            connection.subscriptions.update(event_types)
            
            # Send confirmation
            await self._send_to_connection(connection, WebSocketMessage(
                type=MessageType.SUBSCRIBE,
                data={"subscribed_events": list(connection.subscriptions)}
            ))
            
            return True
    
    async def unsubscribe_from_events(
        self,
        connection_id: str,
        event_types: List[str]
    ) -> bool:
        """
        Unsubscribe connection from specific event types.
        
        Args:
            connection_id: Connection ID
            event_types: List of event types to unsubscribe from
            
        Returns:
            True if unsubscription successful
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False
            
            connection = self._connections[connection_id]
            connection.subscriptions.difference_update(event_types)
            
            # Send confirmation
            await self._send_to_connection(connection, WebSocketMessage(
                type=MessageType.UNSUBSCRIBE,
                data={"subscribed_events": list(connection.subscriptions)}
            ))
            
            return True
    
    async def stream_event(self, event_type: str, event_data: Dict[str, Any]) -> int:
        """
        Stream event to subscribed connections.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Number of connections event was streamed to
        """
        message = WebSocketMessage(
            type=MessageType.EVENT,
            data={"event_type": event_type, "event_data": event_data}
        )
        sent_count = 0
        
        async with self._lock:
            for connection in self._connections.values():
                if (
                    connection.is_active() and
                    event_type in connection.subscriptions
                ):
                    if await self._send_to_connection(connection, message):
                        sent_count += 1
        
        return sent_count
    
    async def _send_to_connection(
        self,
        connection: WebSocketConnection,
        message: WebSocketMessage
    ) -> bool:
        """
        Send message to a specific connection.
        
        Args:
            connection: Target connection
            message: Message to send
            
        Returns:
            True if message sent successfully
        """
        try:
            # Check message size
            message_json = json.dumps(message.to_dict())
            if len(message_json.encode()) > self._config.message_size_limit:
                raise ValueError("Message size exceeds limit")
            
            # Send message
            await connection.websocket.send_text(message_json)
            
            # Update metrics
            self._metrics.messages_sent += 1
            
            return True
            
        except Exception as e:
            self._metrics.errors += 1
            self._logger.error(f"Failed to send message to {connection.connection_id}: {e}")
            
            # Add to dead letter queue
            await self._dead_letter_queue.add(message, str(e))
            
            # Mark connection as error
            connection.status = WebSocketStatus.ERROR
            
            return False
    
    async def _heartbeat_loop(self) -> None:
        """Run heartbeat loop for all connections."""
        while True:
            try:
                await asyncio.sleep(self._config.heartbeat_interval)
                await self._send_heartbeats()
            except Exception as e:
                self._logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(self._config.reconnect_delay)
    
    async def _send_heartbeats(self) -> None:
        """Send heartbeat to all active connections."""
        dead_connections = []
        sent_count = 0
        
        async with self._lock:
            for connection_id, connection in self._connections.items():
                if not connection.is_active():
                    dead_connections.append(connection_id)
                    continue
                
                try:
                    heartbeat = WebSocketMessage(
                        type=MessageType.HEARTBEAT,
                        data={
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "connection_id": connection.connection_id
                        }
                    )
                    
                    if await self._send_to_connection(connection, heartbeat):
                        connection.update_heartbeat()
                        sent_count += 1
                    else:
                        dead_connections.append(connection_id)
                        
                except Exception as e:
                    self._logger.error(f"Heartbeat failed for {connection_id}: {e}")
                    dead_connections.append(connection_id)
            
            # Remove dead connections
            for connection_id in dead_connections:
                await self.disconnect(connection_id, "Heartbeat failed")
        
        if sent_count > 0:
            self._logger.debug(f"Sent heartbeat to {sent_count} connections")
    
    async def _cleanup_loop(self) -> None:
        """Cleanup expired connections and resources."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_expired_connections()
                await self._cleanup_dead_letter_queue()
            except Exception as e:
                self._logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_connections(self) -> None:
        """Remove expired connections based on timeout."""
        expired_connections = []
        current_time = datetime.now(timezone.utc)
        
        async with self._lock:
            for connection_id, connection in self._connections.items():
                # Check if connection has exceeded timeout
                time_since_heartbeat = (
                    current_time - connection.last_heartbeat
                ).total_seconds()
                
                if time_since_heartbeat > self._config.connection_timeout:
                    expired_connections.append(connection_id)
            
            # Remove expired connections
            for connection_id in expired_connections:
                await self.disconnect(connection_id, "Connection timeout")
        
        if expired_connections:
            self._logger.info(f"Cleaned up {len(expired_connections)} expired connections")
    
    async def _cleanup_dead_letter_queue(self) -> None:
        """Clean up old messages in dead letter queue."""
        queue_size = self._dead_letter_queue.size()
        if queue_size > self._config.dead_letter_max_size * 0.8:
            # Remove oldest 20% of messages
            messages_to_remove = int(queue_size * 0.2)
            all_messages = await self._dead_letter_queue.get_all()
            
            # Keep only the newest messages
            await self._dead_letter_queue.clear()
            for message in all_messages[messages_to_remove:]:
                await self._dead_letter_queue.add(*message)
            
            self._logger.info(f"Cleaned up {messages_to_remove} old dead letter messages")
    
    async def close_all_connections(self) -> None:
        """Close all WebSocket connections."""
        connection_ids = list(self._connections.keys())
        
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "Server shutdown")
        
        self._logger.info("Closed all WebSocket connections")
    
    async def shutdown(self) -> None:
        """Shutdown WebSocket manager and cleanup resources."""
        try:
            # Cancel background tasks
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            # Close all connections
            await self.close_all_connections()
            
            # Clear registries
            self._connections.clear()
            self._connection_registry.clear()
            
            # Clear dead letter queue
            await self._dead_letter_queue.clear()
            
            self._logger.info("WebSocket manager shutdown complete")
            
        except Exception as e:
            self._logger.error(f"Error during shutdown: {e}")
    
    def get_metrics(self) -> WebSocketMetrics:
        """Get current WebSocket metrics."""
        # Update active connections count
        self._metrics.active_connections = len(self._connections)
        
        # Calculate average session duration
        if self._metrics.total_connections > 0:
            self._metrics.average_session_duration = (
                self._metrics.total_session_time / self._metrics.total_connections
            )
        
        return self._metrics
    
    async def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection."""
        async with self._lock:
            if connection_id not in self._connections:
                return None
            
            connection = self._connections[connection_id]
            return {
                "connection_id": connection.connection_id,
                "user_id": connection.user_id,
                "workspace_id": connection.workspace_id,
                "status": connection.status.value,
                "connected_at": connection.connected_at.isoformat(),
                "last_heartbeat": connection.last_heartbeat.isoformat(),
                "subscriptions": list(connection.subscriptions),
                "metadata": connection.metadata
            }
    
    async def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get information about all connections."""
        connections_info = []
        
        async with self._lock:
            for connection in self._connections.values():
                connections_info.append({
                    "connection_id": connection.connection_id,
                    "user_id": connection.user_id,
                    "workspace_id": connection.workspace_id,
                    "status": connection.status.value,
                    "connected_at": connection.connected_at.isoformat(),
                    "last_heartbeat": connection.last_heartbeat.isoformat(),
                    "subscriptions": list(connection.subscriptions)
                })
        
        return connections_info
    
    async def get_dead_letter_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from dead letter queue."""
        messages = await self._dead_letter_queue.get_all()
        
        return [
            {
                "message": message[0].to_dict(),
                "error": message[1],
                "timestamp": message[2].isoformat()
            }
            for message in messages
        ]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()