"""
Unit tests for WebSocket system components.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.websocket.manager import WebSocketManager
from app.websocket.streaming import EventStreamer
from app.websocket.client import WebSocketClient
from app.websocket.api import WebSocketAPI
from app.events.bus import EventBus, Event
from app.events.store import EventStore
from app.core.config import get_settings


class TestWebSocketManager:
    """Test cases for WebSocket Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = WebSocketManager()
        self.mock_websocket = Mock()
        self.mock_websocket.send_text = AsyncMock()
        self.mock_websocket.receive_text = AsyncMock()
        self.mock_websocket.close = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_connect_client(self):
        """Test connecting a client."""
        client_id = "test_client_123"
        
        # Connect client
        await self.manager.connect(client_id, self.mock_websocket)
        
        # Verify connection
        assert client_id in self.manager.connections
        assert self.manager.connections[client_id] == self.mock_websocket
        assert client_id in self.manager.client_subscriptions
    
    @pytest.mark.asyncio
    async def test_disconnect_client(self):
        """Test disconnecting a client."""
        client_id = "test_client_123"
        
        # Connect and disconnect client
        await self.manager.connect(client_id, self.mock_websocket)
        await self.manager.disconnect(client_id)
        
        # Verify disconnection
        assert client_id not in self.manager.connections
        assert client_id not in self.manager.client_subscriptions
    
    @pytest.mark.asyncio
    async def test_send_message_to_client(self):
        """Test sending message to specific client."""
        client_id = "test_client_123"
        message = {"type": "test", "data": "hello"}
        
        # Connect client and send message
        await self.manager.connect(client_id, self.mock_websocket)
        await self.manager.send_message(client_id, message)
        
        # Verify message sent
        self.mock_websocket.send_text.assert_called_once_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to all clients."""
        client_id1 = "client1"
        client_id2 = "client2"
        mock_websocket2 = Mock()
        mock_websocket2.send_text = AsyncMock()
        
        message = {"type": "broadcast", "data": "hello all"}
        
        # Connect clients and broadcast
        await self.manager.connect(client_id1, self.mock_websocket)
        await self.manager.connect(client_id2, mock_websocket2)
        await self.manager.broadcast(message)
        
        # Verify both clients received message
        self.mock_websocket.send_text.assert_called_once_with(json.dumps(message))
        mock_websocket2.send_text.assert_called_once_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_subscribe_to_events(self):
        """Test subscribing to events."""
        client_id = "test_client_123"
        event_types = ["execution_started", "execution_completed"]
        
        # Connect client and subscribe
        await self.manager.connect(client_id, self.mock_websocket)
        await self.manager.subscribe(client_id, event_types)
        
        # Verify subscription
        assert client_id in self.manager.client_subscriptions
        assert set(event_types) == set(self.manager.client_subscriptions[client_id])
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_events(self):
        """Test unsubscribing from events."""
        client_id = "test_client_123"
        event_types = ["execution_started", "execution_completed"]
        
        # Connect, subscribe, and unsubscribe
        await self.manager.connect(client_id, self.mock_websocket)
        await self.manager.subscribe(client_id, event_types)
        await self.manager.unsubscribe(client_id, ["execution_started"])
        
        # Verify partial unsubscription
        assert "execution_started" not in self.manager.client_subscriptions[client_id]
        assert "execution_completed" in self.manager.client_subscriptions[client_id]
    
    @pytest.mark.asyncio
    async def test_get_connected_clients(self):
        """Test getting connected clients."""
        client_id1 = "client1"
        client_id2 = "client2"
        mock_websocket2 = Mock()
        
        # Connect clients
        await self.manager.connect(client_id1, self.mock_websocket)
        await self.manager.connect(client_id2, mock_websocket2)
        
        # Get connected clients
        clients = self.manager.get_connected_clients()
        
        # Verify clients
        assert len(clients) == 2
        assert client_id1 in clients
        assert client_id2 in clients
    
    @pytest.mark.asyncio
    async def test_send_event_to_subscribers(self):
        """Test sending event to subscribers."""
        client_id1 = "client1"
        client_id2 = "client2"
        mock_websocket2 = Mock()
        mock_websocket2.send_text = AsyncMock()
        
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Connect clients and subscribe client1 only
        await self.manager.connect(client_id1, self.mock_websocket)
        await self.manager.connect(client_id2, mock_websocket2)
        await self.manager.subscribe(client_id1, ["execution_started"])
        
        # Send event to subscribers
        await self.manager.send_event_to_subscribers(event)
        
        # Verify only subscriber received event
        self.mock_websocket.send_text.assert_called_once()
        mock_websocket2.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_client_error(self):
        """Test handling client errors."""
        client_id = "test_client_123"
        
        # Mock websocket that raises error
        error_websocket = Mock()
        error_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))
        
        # Connect client and send message (should handle error)
        await self.manager.connect(client_id, error_websocket)
        
        # Should not raise exception
        await self.manager.send_message(client_id, {"type": "test"})


class TestEventStreamer:
    """Test cases for Event Streamer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock(spec=WebSocketManager)
        self.streamer = EventStreamer(self.mock_manager)
    
    @pytest.mark.asyncio
    async def test_stream_event(self):
        """Test streaming an event."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Stream event
        await self.streamer.stream_event(event)
        
        # Verify manager was called
        self.mock_manager.send_event_to_subscribers.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_stream_execution_events(self):
        """Test streaming execution events."""
        execution_id = "exec123"
        events = [
            Event(
                id="event1",
                type="node_started",
                data={"node_id": "node1", "execution_id": execution_id},
                timestamp=datetime.now()
            ),
            Event(
                id="event2",
                type="node_completed",
                data={"node_id": "node1", "execution_id": execution_id},
                timestamp=datetime.now()
            )
        ]
        
        # Stream events
        for event in events:
            await self.streamer.stream_event(event)
        
        # Verify all events were streamed
        assert self.mock_manager.send_event_to_subscribers.call_count == 2
    
    @pytest.mark.asyncio
    async def test_filter_events_by_subscription(self):
        """Test filtering events by subscription."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock manager with subscription info
        self.mock_manager.get_subscribed_clients = Mock(return_value=["client1", "client2"])
        
        # Stream event
        await self.streamer.stream_event(event)
        
        # Verify filtered clients
        self.mock_manager.get_subscribed_clients.assert_called_once_with("execution_started")
    
    def test_format_event_message(self):
        """Test formatting event message."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Format event
        message = self.streamer._format_event_message(event)
        
        # Verify format
        assert message["type"] == "event"
        assert message["event_id"] == "event123"
        assert message["event_type"] == "execution_started"
        assert message["data"] == {"execution_id": "exec123"}
        assert "timestamp" in message
    
    @pytest.mark.asyncio
    async def test_handle_stream_error(self):
        """Test handling stream errors."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock manager that raises error
        self.mock_manager.send_event_to_subscribers = AsyncMock(side_effect=Exception("Stream error"))
        
        # Stream event - should not raise exception
        await self.streamer.stream_event(event)


class TestWebSocketClient:
    """Test cases for WebSocket Client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = WebSocketClient("ws://localhost:8000/ws")
    
    @pytest.mark.asyncio
    async def test_connect_to_server(self):
        """Test connecting to server."""
        # Mock websockets connection
        with patch('websockets.connect') as mock_connect:
            mock_websocket = Mock()
            mock_websocket.send = AsyncMock()
            mock_websocket.recv = AsyncMock(return_value='{"type": "ping"}')
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            
            # Connect to server
            await self.client.connect()
            
            # Verify connection
            assert self.client.websocket is not None
            assert self.client.connected is True
    
    @pytest.mark.asyncio
    async def test_disconnect_from_server(self):
        """Test disconnecting from server."""
        # Mock websockets
        mock_websocket = Mock()
        mock_websocket.close = AsyncMock()
        self.client.websocket = mock_websocket
        self.client.connected = True
        
        # Disconnect
        await self.client.disconnect()
        
        # Verify disconnection
        mock_websocket.close.assert_called_once()
        assert self.client.connected is False
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message."""
        # Mock websockets
        mock_websocket = Mock()
        mock_websocket.send = AsyncMock()
        self.client.websocket = mock_websocket
        self.client.connected = True
        
        message = {"type": "test", "data": "hello"}
        
        # Send message
        await self.client.send_message(message)
        
        # Verify message sent
        mock_websocket.send.assert_called_once_with(json.dumps(message))
    
    @pytest.mark.asyncio
    async def test_receive_message(self):
        """Test receiving message."""
        # Mock websockets
        mock_websocket = Mock()
        mock_websocket.recv = AsyncMock(return_value='{"type": "event", "data": "test"}')
        self.client.websocket = mock_websocket
        self.client.connected = True
        
        # Receive message
        message = await self.client.receive_message()
        
        # Verify message received
        assert message["type"] == "event"
        assert message["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_subscribe_to_events(self):
        """Test subscribing to events."""
        # Mock websockets
        mock_websocket = Mock()
        mock_websocket.send = AsyncMock()
        self.client.websocket = mock_websocket
        self.client.connected = True
        
        event_types = ["execution_started", "execution_completed"]
        
        # Subscribe to events
        await self.client.subscribe(event_types)
        
        # Verify subscription message sent
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "subscribe"
        assert set(message["event_types"]) == set(event_types)
    
    @pytest.mark.asyncio
    async def test_handle_connection_error(self):
        """Test handling connection errors."""
        # Mock websockets that raises error
        with patch('websockets.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            # Connect - should handle error
            with pytest.raises(Exception, match="Connection failed"):
                await self.client.connect()
    
    @pytest.mark.asyncio
    async def test_reconnect_on_disconnect(self):
        """Test reconnection on disconnect."""
        # Mock websockets
        with patch('websockets.connect') as mock_connect:
            mock_websocket = Mock()
            mock_websocket.send = AsyncMock()
            mock_websocket.recv = AsyncMock(return_value='{"type": "ping"}')
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            
            # Connect and reconnect
            await self.client.connect()
            await self.client.disconnect()
            await self.client.connect()
            
            # Verify reconnection
            assert self.client.connected is True


class TestWebSocketAPI:
    """Test cases for WebSocket API."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock(spec=WebSocketManager)
        self.mock_streamer = Mock(spec=EventStreamer)
        self.api = WebSocketAPI(self.mock_manager, self.mock_streamer)
    
    @pytest.mark.asyncio
    async def test_handle_websocket_connection(self):
        """Test handling WebSocket connection."""
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock()
        
        # Mock client ID generation
        with patch('uuid.uuid4', return_value='test-client-id'):
            # Handle connection
            await self.api.handle_connection(mock_websocket)
            
            # Verify client connected
            self.mock_manager.connect.assert_called_once_with('test-client-id', mock_websocket)
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self):
        """Test handling subscribe message."""
        client_id = "test_client_123"
        message = {
            "type": "subscribe",
            "event_types": ["execution_started", "execution_completed"]
        }
        
        # Handle subscribe message
        await self.api.handle_message(client_id, message)
        
        # Verify subscription
        self.mock_manager.subscribe.assert_called_once_with(
            client_id, 
            ["execution_started", "execution_completed"]
        )
    
    @pytest.mark.asyncio
    async def test_handle_unsubscribe_message(self):
        """Test handling unsubscribe message."""
        client_id = "test_client_123"
        message = {
            "type": "unsubscribe",
            "event_types": ["execution_started"]
        }
        
        # Handle unsubscribe message
        await self.api.handle_message(client_id, message)
        
        # Verify unsubscription
        self.mock_manager.unsubscribe.assert_called_once_with(
            client_id,
            ["execution_started"]
        )
    
    @pytest.mark.asyncio
    async def test_handle_ping_message(self):
        """Test handling ping message."""
        client_id = "test_client_123"
        message = {"type": "ping"}
        
        # Handle ping message
        await self.api.handle_message(client_id, message)
        
        # Verify pong response
        self.mock_manager.send_message.assert_called_once()
        call_args = self.mock_manager.send_message.call_args[0]
        assert call_args[0] == client_id
        assert call_args[1]["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_handle_invalid_message(self):
        """Test handling invalid message."""
        client_id = "test_client_123"
        message = {"type": "invalid_type"}
        
        # Handle invalid message
        await self.api.handle_message(client_id, message)
        
        # Verify error response
        self.mock_manager.send_message.assert_called_once()
        call_args = self.mock_manager.send_message.call_args[0]
        assert call_args[0] == client_id
        assert call_args[1]["type"] == "error"
    
    @pytest.mark.asyncio
    async def test_get_connection_stats(self):
        """Test getting connection statistics."""
        # Mock manager stats
        self.mock_manager.get_connected_clients.return_value = ["client1", "client2"]
        self.mock_manager.get_subscribed_clients.return_value = ["client1"]
        
        # Get stats
        stats = self.api.get_connection_stats()
        
        # Verify stats
        assert stats["total_connections"] == 2
        assert stats["active_subscriptions"] == 1
        assert "connected_clients" in stats
    
    def test_validate_message_format(self):
        """Test message format validation."""
        # Valid message
        valid_message = {
            "type": "subscribe",
            "event_types": ["execution_started"]
        }
        assert self.api._validate_message(valid_message) is True
        
        # Invalid message (missing type)
        invalid_message = {
            "event_types": ["execution_started"]
        }
        assert self.api._validate_message(invalid_message) is False
        
        # Invalid message (wrong type)
        invalid_message2 = {
            "type": 123,
            "event_types": ["execution_started"]
        }
        assert self.api._validate_message(invalid_message2) is False


if __name__ == "__main__":
    pytest.main([__file__])