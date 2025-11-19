"""
Unit tests for Event System components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

from app.events.bus import EventBus, Event
from app.events.store import EventStore
from app.events.handlers.execution_handlers import ExecutionEventHandler
from app.events.handlers.persistence_handlers import PersistenceEventHandler
from app.events.handlers.websocket_handlers import WebSocketEventHandler


class TestEvent:
    """Test cases for Event class."""
    
    def test_event_creation(self):
        """Test event creation."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123", "node_id": "node1"},
            timestamp=datetime.now()
        )
        
        assert event.id == "event123"
        assert event.type == "execution_started"
        assert event.data["execution_id"] == "exec123"
        assert event.data["node_id"] == "node1"
        assert isinstance(event.timestamp, datetime)
    
    def test_event_serialization(self):
        """Test event serialization."""
        timestamp = datetime.now()
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=timestamp
        )
        
        # Serialize to dict
        event_dict = event.to_dict()
        
        assert event_dict["id"] == "event123"
        assert event_dict["type"] == "execution_started"
        assert event_dict["data"]["execution_id"] == "exec123"
        assert event_dict["timestamp"] == timestamp.isoformat()
    
    def test_event_deserialization(self):
        """Test event deserialization."""
        timestamp = datetime.now()
        event_dict = {
            "id": "event123",
            "type": "execution_started",
            "data": {"execution_id": "exec123"},
            "timestamp": timestamp.isoformat()
        }
        
        # Deserialize from dict
        event = Event.from_dict(event_dict)
        
        assert event.id == "event123"
        assert event.type == "execution_started"
        assert event.data["execution_id"] == "exec123"
        assert event.timestamp == timestamp
    
    def test_event_equality(self):
        """Test event equality."""
        timestamp = datetime.now()
        event1 = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=timestamp
        )
        event2 = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=timestamp
        )
        event3 = Event(
            id="event456",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=timestamp
        )
        
        assert event1 == event2
        assert event1 != event3
    
    def test_event_repr(self):
        """Test event string representation."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        repr_str = repr(event)
        assert "Event(id=event123" in repr_str
        assert "type=execution_started" in repr_str


class TestEventBus:
    """Test cases for Event Bus."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
    
    @pytest.mark.asyncio
    async def test_subscribe_to_event_type(self):
        """Test subscribing to event type."""
        event_type = "execution_started"
        handler = AsyncMock()
        
        # Subscribe to event type
        self.event_bus.subscribe(event_type, handler)
        
        # Verify subscription
        assert event_type in self.event_bus.handlers
        assert handler in self.event_bus.handlers[event_type]
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_event_type(self):
        """Test unsubscribing from event type."""
        event_type = "execution_started"
        handler = AsyncMock()
        
        # Subscribe and unsubscribe
        self.event_bus.subscribe(event_type, handler)
        self.event_bus.unsubscribe(event_type, handler)
        
        # Verify unsubscription
        assert handler not in self.event_bus.handlers[event_type]
    
    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing event."""
        event_type = "execution_started"
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        # Subscribe handlers
        self.event_bus.subscribe(event_type, handler1)
        self.event_bus.subscribe(event_type, handler2)
        
        # Create and publish event
        event = Event(
            id="event123",
            type=event_type,
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        await self.event_bus.publish(event)
        
        # Verify handlers were called
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_event_with_no_handlers(self):
        """Test publishing event with no handlers."""
        event = Event(
            id="event123",
            type="unknown_event",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Should not raise exception
        await self.event_bus.publish(event)
    
    @pytest.mark.asyncio
    async def test_publish_event_with_handler_error(self):
        """Test publishing event with handler error."""
        event_type = "execution_started"
        good_handler = AsyncMock()
        bad_handler = AsyncMock(side_effect=Exception("Handler error"))
        
        # Subscribe handlers
        self.event_bus.subscribe(event_type, good_handler)
        self.event_bus.subscribe(event_type, bad_handler)
        
        # Create and publish event
        event = Event(
            id="event123",
            type=event_type,
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Should not raise exception, good handler should still be called
        await self.event_bus.publish(event)
        good_handler.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_get_handler_count(self):
        """Test getting handler count."""
        event_type = "execution_started"
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        # Subscribe handlers
        self.event_bus.subscribe(event_type, handler1)
        self.event_bus.subscribe(event_type, handler2)
        
        # Get handler count
        count = self.event_bus.get_handler_count(event_type)
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_clear_handlers(self):
        """Test clearing handlers."""
        event_type = "execution_started"
        handler = AsyncMock()
        
        # Subscribe handler and clear
        self.event_bus.subscribe(event_type, handler)
        self.event_bus.clear_handlers(event_type)
        
        # Verify handlers cleared
        assert len(self.event_bus.handlers[event_type]) == 0
    
    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test wildcard subscription."""
        handler = AsyncMock()
        
        # Subscribe to all events
        self.event_bus.subscribe("*", handler)
        
        # Publish different event types
        event1 = Event(id="e1", type="execution_started", data={}, timestamp=datetime.now())
        event2 = Event(id="e2", type="execution_completed", data={}, timestamp=datetime.now())
        
        await self.event_bus.publish(event1)
        await self.event_bus.publish(event2)
        
        # Verify handler called for both events
        assert handler.call_count == 2


class TestEventStore:
    """Test cases for Event Store."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.event_store = EventStore(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_store_event(self):
        """Test storing event."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock database operations
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Store event
        stored_event = await self.event_store.store_event(event)
        
        # Verify database operations
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        assert stored_event == event
    
    @pytest.mark.asyncio
    async def test_get_event_by_id(self):
        """Test getting event by ID."""
        event_id = "event123"
        
        # Mock database query
        mock_event = Mock()
        mock_event.id = event_id
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_event
        
        # Get event
        event = await self.event_store.get_event(event_id)
        
        # Verify query
        assert event == mock_event
        self.mock_db.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_by_type(self):
        """Test getting events by type."""
        event_type = "execution_started"
        limit = 10
        
        # Mock database query
        mock_events = [Mock(), Mock()]
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_events
        
        # Get events
        events = await self.event_store.get_events_by_type(event_type, limit)
        
        # Verify query
        assert events == mock_events
        self.mock_db.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_by_execution_id(self):
        """Test getting events by execution ID."""
        execution_id = "exec123"
        
        # Mock database query
        mock_events = [Mock(), Mock()]
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_events
        
        # Get events
        events = await self.event_store.get_events_by_execution_id(execution_id)
        
        # Verify query
        assert events == mock_events
        self.mock_db.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_in_time_range(self):
        """Test getting events in time range."""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        # Mock database query
        mock_events = [Mock(), Mock()]
        self.mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = mock_events
        
        # Get events
        events = await self.event_store.get_events_in_time_range(start_time, end_time)
        
        # Verify query
        assert events == mock_events
        self.mock_db.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_old_events(self):
        """Test deleting old events."""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # Mock database operations
        self.mock_db.query.return_value.filter.return_value.delete.return_value = 100
        self.mock_db.commit = Mock()
        
        # Delete old events
        deleted_count = await self.event_store.delete_old_events(cutoff_date)
        
        # Verify deletion
        assert deleted_count == 100
        self.mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_event_statistics(self):
        """Test getting event statistics."""
        # Mock database queries
        self.mock_db.query.return_value.count.return_value = 1000
        self.mock_db.query.return_value.group_by.return_value.all.return_value = [
            ("execution_started", 400),
            ("execution_completed", 300),
            ("node_started", 200),
            ("node_completed", 100)
        ]
        
        # Get statistics
        stats = await self.event_store.get_event_statistics()
        
        # Verify statistics
        assert stats["total_events"] == 1000
        assert stats["event_types"]["execution_started"] == 400
        assert stats["event_types"]["execution_completed"] == 300


class TestExecutionEventHandler:
    """Test cases for Execution Event Handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context_manager = Mock()
        self.mock_resource_manager = Mock()
        self.handler = ExecutionEventHandler(
            self.mock_context_manager,
            self.mock_resource_manager
        )
    
    @pytest.mark.asyncio
    async def test_handle_execution_started(self):
        """Test handling execution started event."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123", "agent_id": "agent123"},
            timestamp=datetime.now()
        )
        
        # Mock context manager
        mock_context = Mock()
        self.mock_context_manager.get_context.return_value = mock_context
        
        # Handle event
        await self.handler.handle(event)
        
        # Verify context updated
        self.mock_context_manager.update_context.assert_called_once_with(
            "exec123",
            {"status": "running", "start_time": event.timestamp}
        )
    
    @pytest.mark.asyncio
    async def test_handle_execution_completed(self):
        """Test handling execution completed event."""
        event = Event(
            id="event123",
            type="execution_completed",
            data={"execution_id": "exec123", "output_data": {"result": "success"}},
            timestamp=datetime.now()
        )
        
        # Handle event
        await self.handler.handle(event)
        
        # Verify context completed
        self.mock_context_manager.complete_context.assert_called_once_with(
            "exec123",
            "completed",
            {"result": "success"}
        )
    
    @pytest.mark.asyncio
    async def test_handle_execution_failed(self):
        """Test handling execution failed event."""
        event = Event(
            id="event123",
            type="execution_failed",
            data={"execution_id": "exec123", "error": "Something went wrong"},
            timestamp=datetime.now()
        )
        
        # Handle event
        await self.handler.handle(event)
        
        # Verify context completed with error
        self.mock_context_manager.complete_context.assert_called_once_with(
            "exec123",
            "failed",
            {"error": "Something went wrong"}
        )
    
    @pytest.mark.asyncio
    async def test_handle_node_started(self):
        """Test handling node started event."""
        event = Event(
            id="event123",
            type="node_started",
            data={"execution_id": "exec123", "node_id": "node1"},
            timestamp=datetime.now()
        )
        
        # Handle event
        await self.handler.handle(event)
        
        # Verify context updated
        self.mock_context_manager.update_context.assert_called_once_with(
            "exec123",
            {"current_node": "node1", "node_start_time": event.timestamp}
        )
    
    @pytest.mark.asyncio
    async def test_handle_unknown_event_type(self):
        """Test handling unknown event type."""
        event = Event(
            id="event123",
            type="unknown_event",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Handle event - should not raise exception
        await self.handler.handle(event)
    
    @pytest.mark.asyncio
    async def test_handle_event_with_missing_execution_id(self):
        """Test handling event with missing execution ID."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"agent_id": "agent123"},  # Missing execution_id
            timestamp=datetime.now()
        )
        
        # Handle event - should not raise exception
        await self.handler.handle(event)


class TestPersistenceEventHandler:
    """Test cases for Persistence Event Handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_event_store = Mock(spec=EventStore)
        self.handler = PersistenceEventHandler(self.mock_event_store)
    
    @pytest.mark.asyncio
    async def test_handle_event_persistence(self):
        """Test event persistence."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock event store
        self.mock_event_store.store_event = AsyncMock(return_value=event)
        
        # Handle event
        await self.handler.handle(event)
        
        # Verify event stored
        self.mock_event_store.store_event.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_handle_persistence_error(self):
        """Test handling persistence error."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock event store that raises error
        self.mock_event_store.store_event = AsyncMock(side_effect=Exception("Database error"))
        
        # Handle event - should not raise exception
        await self.handler.handle(event)
    
    @pytest.mark.asyncio
    async def test_filter_events_for_persistence(self):
        """Test filtering events for persistence."""
        # Test event that should be persisted
        important_event = Event(
            id="event1",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Test event that should not be persisted
        debug_event = Event(
            id="event2",
            type="debug_log",
            data={"message": "Debug info"},
            timestamp=datetime.now()
        )
        
        # Check if events should be persisted
        assert self.handler._should_persist(important_event) is True
        assert self.handler._should_persist(debug_event) is False


class TestWebSocketEventHandler:
    """Test cases for WebSocket Event Handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_streamer = Mock()
        self.handler = WebSocketEventHandler(self.mock_streamer)
    
    @pytest.mark.asyncio
    async def test_handle_websocket_event(self):
        """Test WebSocket event handling."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock streamer
        self.mock_streamer.stream_event = AsyncMock()
        
        # Handle event
        await self.handler.handle(event)
        
        # Verify event streamed
        self.mock_streamer.stream_event.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_handle_websocket_error(self):
        """Test handling WebSocket error."""
        event = Event(
            id="event123",
            type="execution_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Mock streamer that raises error
        self.mock_streamer.stream_event = AsyncMock(side_effect=Exception("WebSocket error"))
        
        # Handle event - should not raise exception
        await self.handler.handle(event)
    
    @pytest.mark.asyncio
    async def test_filter_events_for_websocket(self):
        """Test filtering events for WebSocket."""
        # Test event that should be streamed
        real_time_event = Event(
            id="event1",
            type="node_started",
            data={"execution_id": "exec123"},
            timestamp=datetime.now()
        )
        
        # Test event that should not be streamed
        internal_event = Event(
            id="event2",
            type="internal_metrics",
            data={"metrics": "data"},
            timestamp=datetime.now()
        )
        
        # Check if events should be streamed
        assert self.handler._should_stream(real_time_event) is True
        assert self.handler._should_stream(internal_event) is False


if __name__ == "__main__":
    pytest.main([__file__])