"""
WebSocket Client Implementation

This module provides a WebSocket client for connecting to external WebSocket servers
and consuming real-time events from the execution system.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Callable, List, AsyncIterator
import json
import asyncio
import logging
from datetime import datetime, timezone

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.execution.models import ExecutionEvent, EventType

logger = get_logger(__name__)


class WebSocketClient:
    """WebSocket client for connecting to external WebSocket servers."""
    
    def __init__(self):
        """Initialize WebSocket client."""
        self.logger = logger
        self.settings = get_settings()
        self._connection: Optional[WebSocketClientProtocol] = None
        self._connected = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 1.0
        self._running = False
    
    async def connect(
        self, 
        url: str,
        headers: Optional[Dict[str, str]] = None,
        auto_reconnect: bool = True
    ) -> bool:
        """Connect to WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets library is not available. Install it to use WebSocket client.")
        
        try:
            self.logger.info(f"Connecting to WebSocket: {url}")
            
            # Set default headers
            if headers is None:
                headers = {
                    "User-Agent": f"PromptFlow-WebSocket-Client/{self.settings.VERSION}",
                    "Origin": self.settings.FRONTEND_URL,
                }
            
            # Connect to WebSocket
            self._connection = await websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            self.logger.info(f"Connected to WebSocket: {url}")
            
            # Start listening for messages if auto-reconnect is enabled
            if auto_reconnect:
                asyncio.create_task(self._listen_for_messages(url, headers, auto_reconnect))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to WebSocket {url}: {e}")
            if auto_reconnect:
                await self._handle_reconnect(url, headers, auto_reconnect)
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        try:
            self._running = False
            self._connected = False
            
            if self._connection:
                await self._connection.close()
                self._connection = None
            
            self.logger.info("Disconnected from WebSocket")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from WebSocket: {e}")
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message to WebSocket server."""
        try:
            if not self._connected or not self._connection:
                self.logger.warning("Not connected to WebSocket server")
                return False
            
            # Serialize message
            message_str = json.dumps(message, default=str)
            
            # Send message
            await self._connection.send(message_str)
            self.logger.debug(f"Sent message: {message}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    async def send_event(self, event: ExecutionEvent) -> bool:
        """Send execution event to WebSocket server."""
        try:
            event_data = {
                "type": "execution_event",
                "data": event.to_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return await self.send_message(event_data)
            
        except Exception as e:
            self.logger.error(f"Error sending execution event: {e}")
            return False
    
    def add_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add event handler for specific event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        self.logger.debug(f"Added handler for event type: {event_type}")
    
    def remove_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Remove event handler for specific event type."""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                self.logger.debug(f"Removed handler for event type: {event_type}")
            except ValueError:
                pass
    
    async def _listen_for_messages(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]], 
        auto_reconnect: bool
    ) -> None:
        """Listen for messages from WebSocket server."""
        self._running = True
        
        try:
            while self._running and self._connected and self._connection:
                try:
                    # Receive message
                    message_str = await self._connection.recv()
                    
                    # Parse message
                    try:
                        message = json.loads(message_str)
                        await self._handle_message(message)
                    except json.JSONDecodeError:
                        self.logger.warning(f"Received invalid JSON: {message_str}")
                    
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving message: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error in message listener: {e}")
        finally:
            self._running = False
            
            # Handle reconnection if enabled
            if auto_reconnect:
                await self._handle_reconnect(url, headers, auto_reconnect)
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle received message."""
        try:
            message_type = message.get("type", "unknown")
            
            # Log message
            self.logger.debug(f"Received message type: {message_type}")
            
            # Call event handlers
            if message_type in self._event_handlers:
                for handler in self._event_handlers[message_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        self.logger.error(f"Error in event handler: {e}")
            
            # Handle specific message types
            if message_type == "execution_event":
                await self._handle_execution_event(message.get("data", {}))
            elif message_type == "ping":
                await self.send_message({"type": "pong"})
            elif message_type == "error":
                self.logger.error(f"Received error message: {message.get('message')}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _handle_execution_event(self, event_data: Dict[str, Any]) -> None:
        """Handle execution event message."""
        try:
            # Convert to domain event
            event = ExecutionEvent(
                event_id=event_data.get("event_id", ""),
                event_type=EventType(event_data.get("event_type", "execution_started")),
                execution_id=event_data.get("execution_id", ""),
                node_id=event_data.get("node_id"),
                timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.now(timezone.utc).isoformat())),
                data=event_data.get("data", {}),
                metadata=event_data.get("metadata", {})
            )
            
            # Log event
            self.logger.info(f"Received execution event: {event.event_type.value} for {event.execution_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling execution event: {e}")
    
    async def _handle_reconnect(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]], 
        auto_reconnect: bool
    ) -> None:
        """Handle reconnection logic."""
        if not auto_reconnect:
            return
        
        while self._reconnect_attempts < self._max_reconnect_attempts:
            try:
                self._reconnect_attempts += 1
                self.logger.info(f"Attempting to reconnect ({self._reconnect_attempts}/{self._max_reconnect_attempts})")
                
                # Wait before reconnecting
                await asyncio.sleep(self._reconnect_delay)
                
                # Try to reconnect
                if await self.connect(url, headers, auto_reconnect=False):
                    self.logger.info("Reconnected successfully")
                    # Start listening again
                    asyncio.create_task(self._listen_for_messages(url, headers, auto_reconnect))
                    return
                
                # Exponential backoff
                self._reconnect_delay *= 2
                
            except Exception as e:
                self.logger.error(f"Reconnection attempt failed: {e}")
        
        self.logger.error("Max reconnection attempts reached")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to WebSocket server."""
        return self._connected
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "connected": self._connected,
            "running": self._running,
            "reconnect_attempts": self._reconnect_attempts,
            "max_reconnect_attempts": self._max_reconnect_attempts,
            "reconnect_delay": self._reconnect_delay,
        }


class PromptFlowWebSocketClient(WebSocketClient):
    """Specialized WebSocket client for PromptFlow execution events."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize PromptFlow WebSocket client."""
        super().__init__()
        self.base_url = base_url or f"ws://localhost:{self.settings.API_PORT}/api/v1/ws/connect"
        self.execution_id: Optional[str] = None
        self.subscribed_events: List[str] = []
    
    async def connect_to_execution(self, execution_id: str) -> bool:
        """Connect to specific execution stream."""
        try:
            self.execution_id = execution_id
            url = f"{self.base_url}?execution_id={execution_id}"
            
            headers = {
                "User-Agent": f"PromptFlow-Execution-Client/{self.settings.VERSION}",
                "Execution-ID": execution_id,
            }
            
            return await self.connect(url, headers)
            
        except Exception as e:
            self.logger.error(f"Error connecting to execution {execution_id}: {e}")
            return False
    
    async def subscribe_to_events(self, event_types: List[str]) -> bool:
        """Subscribe to specific event types."""
        try:
            message = {
                "type": "subscribe",
                "event_types": event_types
            }
            
            success = await self.send_message(message)
            if success:
                self.subscribed_events.extend(event_types)
                self.logger.info(f"Subscribed to events: {event_types}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error subscribing to events: {e}")
            return False
    
    async def unsubscribe_from_events(self, event_types: List[str]) -> bool:
        """Unsubscribe from specific event types."""
        try:
            message = {
                "type": "unsubscribe",
                "event_types": event_types
            }
            
            success = await self.send_message(message)
            if success:
                for event_type in event_types:
                    if event_type in self.subscribed_events:
                        self.subscribed_events.remove(event_type)
                self.logger.info(f"Unsubscribed from events: {event_types}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from events: {e}")
            return False
    
    async def request_execution_status(self, execution_id: Optional[str] = None) -> bool:
        """Request current execution status."""
        try:
            target_execution_id = execution_id or self.execution_id
            if not target_execution_id:
                self.logger.error("No execution ID specified")
                return False
            
            message = {
                "type": "get_status",
                "execution_id": target_execution_id
            }
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error requesting execution status: {e}")
            return False


# Factory function
def create_websocket_client() -> WebSocketClient:
    """Create WebSocket client instance."""
    return WebSocketClient()


def create_promptflow_client(base_url: Optional[str] = None) -> PromptFlowWebSocketClient:
    """Create PromptFlow WebSocket client instance."""
    return PromptFlowWebSocketClient(base_url)


# Utility functions
async def test_websocket_connection(url: str) -> bool:
    """Test WebSocket connection."""
    try:
        if not WEBSOCKETS_AVAILABLE:
            return False
        
        async with websockets.connect(url, timeout=5) as websocket:
            await websocket.ping()
            return True
            
    except Exception as e:
        logger.error(f"WebSocket connection test failed: {e}")
        return False


async def stream_events(
    url: str,
    event_types: Optional[List[str]] = None,
    timeout: Optional[float] = None
) -> AsyncIterator[Dict[str, Any]]:
    """Stream events from WebSocket server."""
    try:
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets library is not available")
        
        async with websockets.connect(url) as websocket:
            # Subscribe to events if specified
            if event_types:
                subscribe_message = {
                    "type": "subscribe",
                    "event_types": event_types
                }
                await websocket.send(json.dumps(subscribe_message))
            
            # Stream messages
            while True:
                try:
                    message_str = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=timeout
                    )
                    message = json.loads(message_str)
                    yield message
                    
                except asyncio.TimeoutError:
                    break
                except websockets.exceptions.ConnectionClosed:
                    break
                    
    except Exception as e:
        logger.error(f"Error streaming events: {e}")
        raise