"""
Event System Integration Tests

This module provides comprehensive tests for the Phase 3 Day 5 event system
including event bus, event store, and event handlers.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
import uuid

from app.events import (
    EventBus,
    EventBusConfig,
    EventStore,
    EventStoreConfig,
    get_event_bus,
    get_event_store,
    configure_event_bus,
    configure_event_store,
)
from app.events.handlers import (
    ExecutionEventHandler,
    NodeEventHandler,
    MetricsEventHandler,
    WebSocketEventHandler,
    PersistenceEventHandler,
    create_execution_handlers,
    create_websocket_handlers,
    create_persistence_handlers,
)
from app.domain.execution.models import (
    ExecutionEvent,
    EventType,
    ExecutionStatus,
    NodeStatus,
    ExecutionStarted,
    ExecutionCompleted,
    NodeExecutionCompleted,
)
from app.nodes import (
    NodeFactory,
    InputNode,
    OutputNode,
    LLMNode,
    NodeType,
    ExecutionMode,
    NodeConfiguration,
)
from app.execution.compiler.dag_compiler import DAGCompiler
from app.execution.validation.graph_validator import GraphValidator


class TestEventBus:
    """Test cases for Event Bus implementation."""
    
    @pytest.fixture
    def event_bus_config(self):
        """Create event bus configuration for testing."""
        return EventBusConfig(
            max_handlers=100,
            enable_metrics=True,
            enable_tracing=True,
        )
    
    @pytest.fixture
    def event_bus(self, event_bus_config):
        """Create event bus instance for testing."""
        return EventBus(event_bus_config)
    
    @pytest.fixture
    def sample_event(self):
        """Create sample execution event for testing."""
        return ExecutionEvent(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=str(uuid.uuid4()),
            node_id=None,
            timestamp=datetime.now(timezone.utc),
            data={"test": "data"},
            metadata={"source": "test"},
        )
    
    def test_event_bus_creation(self, event_bus):
        """Test event bus creation."""
        assert event_bus is not None
        assert event_bus._config.max_handlers == 100
        assert event_bus._config.enable_metrics is True
    
    @pytest.mark.asyncio
    async def test_event_subscription(self, event_bus, sample_event):
        """Test event subscription and publishing."""
        received_events = []
        
        async def test_handler(event):
            received_events.append(event)
        
        # Subscribe to events
        event_bus.subscribe(EventType.EXECUTION_STARTED, test_handler)
        
        # Publish event
        await event_bus.publish(sample_event)
        
        # Wait for async processing
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.EXECUTION_STARTED
        assert received_events[0].data["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_event_unsubscription(self, event_bus, sample_event):
        """Test event unsubscription."""
        received_events = []
        
        async def test_handler(event):
            received_events.append(event)
        
        # Subscribe and then unsubscribe
        event_bus.subscribe(EventType.EXECUTION_STARTED, test_handler)
        event_bus.unsubscribe(EventType.EXECUTION_STARTED, test_handler)
        
        # Publish event
        await event_bus.publish(sample_event)
        
        # Wait for async processing
        await asyncio.sleep(0.1)
        
        # Verify no events were received
        assert len(received_events) == 0
    
    @pytest.mark.asyncio
    async def test_event_metrics(self, event_bus, sample_event):
        """Test event bus metrics collection."""
        async def test_handler(event):
            pass
        
        # Subscribe and publish events
        event_bus.subscribe(EventType.EXECUTION_STARTED, test_handler)
        await event_bus.publish(sample_event)
        await asyncio.sleep(0.1)
        
        # Check metrics
        metrics = event_bus.get_metrics()
        assert metrics["events_published"] == 1
        assert metrics["events_processed"] == 1
        assert metrics["handlers_count"] == 1


class TestEventStore:
    """Test cases for Event Store implementation."""
    
    @pytest.fixture
    def event_store_config(self):
        """Create event store configuration for testing."""
        return EventStoreConfig(
            backend="memory",
            max_events_in_memory=1000,
            enable_snapshots=True,
            snapshot_interval=10,
        )
    
    @pytest.fixture
    def event_store(self, event_store_config):
        """Create event store instance for testing."""
        return EventStore(event_store_config)
    
    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        execution_id = str(uuid.uuid4())
        return [
            ExecutionEvent(
                event_type=EventType.EXECUTION_STARTED,
                execution_id=execution_id,
                timestamp=datetime.now(timezone.utc),
                data={"step": i},
            )
            for i in range(5)
        ]
    
    @pytest.mark.asyncio
    async def test_event_storage(self, event_store, sample_events):
        """Test event storage and retrieval."""
        execution_id = sample_events[0].execution_id
        
        # Store events
        for event in sample_events:
            await event_store.store_event(event)
        
        # Retrieve events
        retrieved_events = await event_store.get_events(execution_id)
        
        assert len(retrieved_events) == 5
        assert all(event.execution_id == execution_id for event in retrieved_events)
    
    @pytest.mark.asyncio
    async def test_event_filtering(self, event_store, sample_events):
        """Test event filtering by version."""
        execution_id = sample_events[0].execution_id
        
        # Store events
        for event in sample_events:
            await event_store.store_event(event)
        
        # Get events from version 2
        filtered_events = await event_store.get_events(execution_id, from_version=2)
        
        assert len(filtered_events) == 4  # events 2, 3, 4, 5
    
    @pytest.mark.asyncio
    async def test_event_type_filtering(self, event_store):
        """Test filtering events by type."""
        execution_id = str(uuid.uuid4())
        
        # Store different event types
        events = [
            ExecutionEvent(
                event_type=EventType.NODE_STARTED,
                execution_id=execution_id,
                timestamp=datetime.now(timezone.utc),
            ),
            ExecutionEvent(
                event_type=EventType.NODE_COMPLETED,
                execution_id=execution_id,
                timestamp=datetime.now(timezone.utc),
            ),
        ]
        
        for event in events:
            await event_store.store_event(event)
        
        # Get events by type
        node_started_events = await event_store.get_events_by_type(EventType.NODE_STARTED)
        node_completed_events = await event_store.get_events_by_type(EventType.NODE_COMPLETED)
        
        assert len(node_started_events) == 1
        assert len(node_completed_events) == 1
        assert node_started_events[0].event_type == EventType.NODE_STARTED
        assert node_completed_events[0].event_type == EventType.NODE_COMPLETED


class TestNodeImplementations:
    """Test cases for node implementations."""
    
    @pytest.fixture
    def node_factory(self):
        """Create node factory for testing."""
        return NodeFactory()
    
    @pytest.fixture
    def input_node_config(self):
        """Create input node configuration."""
        return NodeConfiguration(
            node_id="test_input",
            node_type="input",
            config={
                "input_type": "text",
                "required": True,
                "placeholder": "Enter input...",
            }
        )
    
    @pytest.fixture
    def output_node_config(self):
        """Create output node configuration."""
        return NodeConfiguration(
            node_id="test_output",
            node_type="output",
            config={
                "output_type": "json",
                "include_metadata": True,
            }
        )
    
    @pytest.mark.asyncio
    async def test_input_node_execution(self, node_factory, input_node_config):
        """Test input node execution."""
        # Create input node
        input_node = node_factory.create_node(
            NodeType.INPUT,
            "test_input",
            input_node_config
        )
        
        # Create input data
        from app.execution.nodes.base_node import NodeInput, NodeContext
        input_data = NodeInput(
            data={"value": "test input"},
            metadata={"source": "test"},
        )
        
        context = NodeContext(
            node_id="test_input",
            execution_id=str(uuid.uuid4()),
            workspace_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config=None,  # Would be ExecutionConfig in real scenario
        )
        
        # Execute node
        output = await input_node.run(input_data, context)
        
        # Verify output
        assert output.data["value"] == "test input"
        assert output.data["type"] == "text"
        assert output.error is None
        assert output.metadata["node_type"] == "input"
    
    @pytest.mark.asyncio
    async def test_output_node_execution(self, node_factory, output_node_config):
        """Test output node execution."""
        # Create output node
        output_node = node_factory.create_node(
            NodeType.OUTPUT,
            "test_output",
            output_node_config
        )
        
        # Create input data
        from app.execution.nodes.base_node import NodeInput, NodeContext
        input_data = NodeInput(
            data={"result": {"message": "Hello, World!", "count": 42}},
            metadata={"source": "test"},
        )
        
        context = NodeContext(
            node_id="test_output",
            execution_id=str(uuid.uuid4()),
            workspace_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config=None,  # Would be ExecutionConfig in real scenario
        )
        
        # Execute node
        output = await output_node.run(input_data, context)
        
        # Verify output
        assert "result" in output.data
        assert output.data["type"] == "json"
        assert output.error is None
        assert output.metadata["node_type"] == "output"
    
    def test_node_factory_registration(self, node_factory):
        """Test node factory registration."""
        # Check available node types
        available_types = node_factory.get_available_node_types()
        
        assert NodeType.INPUT in available_types
        assert NodeType.OUTPUT in available_types
        assert NodeType.LLM in available_types
        assert NodeType.RETRIEVAL in available_types
        assert NodeType.TOOL in available_types
        
        # Check node type support
        assert node_factory.is_node_type_supported(NodeType.INPUT)
        assert node_factory.is_node_type_supported(NodeType.OUTPUT)


class TestEventHandlers:
    """Test cases for event handlers."""
    
    @pytest.fixture
    def handler_config(self):
        """Create handler configuration."""
        from app.events.handlers.execution_handlers import HandlerConfig
        return HandlerConfig(
            enabled=True,
            retry_attempts=2,
            timeout=5.0,
            enable_metrics=True,
        )
    
    @pytest.fixture
    def sample_execution_event(self):
        """Create sample execution event."""
        return ExecutionEvent(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            data={"test": "execution"},
        )
    
    @pytest.fixture
    def sample_node_event(self):
        """Create sample node event."""
        return ExecutionEvent(
            event_type=EventType.NODE_COMPLETED,
            execution_id=str(uuid.uuid4()),
            node_id="test_node",
            timestamp=datetime.now(timezone.utc),
            data={"execution_time": 1.5},
        )
    
    @pytest.mark.asyncio
    async def test_execution_event_handler(self, handler_config, sample_execution_event):
        """Test execution event handler."""
        handler = ExecutionEventHandler(handler_config)
        
        # Handle event
        await handler.handle_with_retry(sample_execution_event)
        
        # Check execution state
        state = handler.get_execution_state(sample_execution_event.execution_id)
        assert state is not None
        assert state["status"] == ExecutionStatus.RUNNING
        assert len(state["events"]) == 1
    
    @pytest.mark.asyncio
    async def test_node_event_handler(self, handler_config, sample_node_event):
        """Test node event handler."""
        handler = NodeEventHandler(handler_config)
        
        # Handle event
        await handler.handle_with_retry(sample_node_event)
        
        # Check node state
        state = handler.get_node_state(sample_node_event.node_id)
        assert state is not None
        assert state["status"] == NodeStatus.COMPLETED
        assert len(state["events"]) == 1
    
    @pytest.mark.asyncio
    async def test_metrics_event_handler(self, handler_config, sample_execution_event, sample_node_event):
        """Test metrics event handler."""
        handler = MetricsEventHandler(handler_config)
        
        # Handle events
        await handler.handle_with_retry(sample_execution_event)
        await handler.handle_with_retry(sample_node_event)
        
        # Check global metrics
        metrics = handler.get_global_metrics()
        assert metrics["total_executions"] == 1
        assert metrics["total_nodes"] == 1
        assert metrics["successful_nodes"] == 1


class TestIntegration:
    """Integration tests for the complete event system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_event_flow(self):
        """Test complete event flow from node execution to event handling."""
        # Create components
        event_bus = EventBus(EventBusConfig())
        event_store = EventStore(EventStoreConfig())
        node_factory = NodeFactory()
        
        # Create handlers
        from app.events.handlers.execution_handlers import HandlerConfig
        handler_config = HandlerConfig()
        handlers = create_execution_handlers(handler_config)
        
        # Subscribe handlers to event bus
        for handler in handlers:
            event_bus.subscribe(EventType.EXECUTION_STARTED, handler.handle_with_retry)
            event_bus.subscribe(EventType.NODE_COMPLETED, handler.handle_with_retry)
        
        # Create and configure nodes
        input_config = NodeConfiguration(
            node_id="test_input",
            node_type="input",
            config={"input_type": "text"}
        )
        
        output_config = NodeConfiguration(
            node_id="test_output", 
            node_type="output",
            config={"output_type": "json"}
        )
        
        input_node = node_factory.create_node(NodeType.INPUT, "test_input", input_config)
        output_node = node_factory.create_node(NodeType.OUTPUT, "test_output", output_config)
        
        # Create execution context
        execution_id = str(uuid.uuid4())
        from app.execution.nodes.base_node import NodeInput, NodeContext
        
        # Start execution
        start_event = ExecutionEvent(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=execution_id,
            timestamp=datetime.now(timezone.utc),
        )
        
        await event_bus.publish(start_event)
        await event_store.store_event(start_event)
        
        # Execute input node
        input_context = NodeContext(
            node_id="test_input",
            execution_id=execution_id,
            workspace_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config=None,
        )
        
        input_data = NodeInput(data={"value": "test data"})
        input_output = await input_node.run(input_data, input_context)
        
        # Create node completion event
        node_event = ExecutionEvent(
            event_type=EventType.NODE_COMPLETED,
            execution_id=execution_id,
            node_id="test_input",
            timestamp=datetime.now(timezone.utc),
            data={"execution_time": input_output.execution_time},
        )
        
        await event_bus.publish(node_event)
        await event_store.store_event(node_event)
        
        # Execute output node
        output_context = NodeContext(
            node_id="test_output",
            execution_id=execution_id,
            workspace_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config=None,
            dependencies={"test_input": input_output},
        )
        
        output_data = NodeInput(data={"result": input_output.data})
        output_output = await output_node.run(output_data, output_context)
        
        # Complete execution
        complete_event = ExecutionEvent(
            event_type=EventType.EXECUTION_COMPLETED,
            execution_id=execution_id,
            timestamp=datetime.now(timezone.utc),
        )
        
        await event_bus.publish(complete_event)
        await event_store.store_event(complete_event)
        
        # Wait for async processing
        await asyncio.sleep(0.1)
        
        # Verify results
        stored_events = await event_store.get_events(execution_id)
        assert len(stored_events) == 3
        
        # Check handler states
        execution_handler = handlers[0]  # ExecutionEventHandler
        execution_state = execution_handler.get_execution_state(execution_id)
        assert execution_state is not None
        assert execution_state["status"] == ExecutionStatus.COMPLETED
        
        # Check metrics
        metrics_handler = handlers[2]  # MetricsEventHandler
        metrics = metrics_handler.get_global_metrics()
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["total_nodes"] == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])