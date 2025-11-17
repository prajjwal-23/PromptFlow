"""
Manual Event System Testing Script

This script provides a simple way to manually test the Phase 3 Day 5 event system
without requiring complex test setup. Run this script to verify the implementation.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
import uuid

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.events import EventBus, EventStore, get_event_bus, get_event_store
    from app.events.handlers import ExecutionEventHandler, NodeEventHandler, MetricsEventHandler
    from app.domain.execution.models import ExecutionEvent, EventType
    from app.nodes import NodeFactory, NodeType
    from app.execution.nodes.base_node import NodeInput, NodeContext
    print("SUCCESS: All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the backend directory")
    sys.exit(1)


class EventSystemTester:
    """Manual tester for the event system."""
    
    def __init__(self):
        self.test_results = []
        self.event_bus = None
        self.event_store = None
        self.node_factory = None
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if success else "FAIL"
        self.test_results.append((test_name, success, message))
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
    
    async def test_event_bus(self):
        """Test event bus functionality."""
        print("\nTesting Event Bus...")
        
        try:
            # Create event bus
            self.event_bus = get_event_bus()
            self.log_test("Event Bus Creation", True)
            
            # Test event subscription
            received_events = []
            
            async def test_handler(event):
                received_events.append(event)
                print(f"    Received event: {event.event_type.value}")
            
            await self.event_bus.subscribe(EventType.EXECUTION_STARTED, test_handler)
            self.log_test("Event Subscription", True)
            
            # Test event publishing
            test_event = ExecutionEvent(
                event_type=EventType.EXECUTION_STARTED,
                execution_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                data={"test": "manual_test"},
            )
            
            await self.event_bus.publish(test_event)
            await asyncio.sleep(0.1)  # Wait for async processing
            
            if len(received_events) == 1:
                self.log_test("Event Publishing", True, f"Received {len(received_events)} event")
            else:
                self.log_test("Event Publishing", False, f"Expected 1 event, got {len(received_events)}")
            
            # Test metrics
            metrics = self.event_bus.get_metrics()
            self.log_test("Event Bus Metrics", True, f"Published: {metrics.get('events_published', 0)}")
            
        except Exception as e:
            self.log_test("Event Bus", False, str(e))
    
    async def test_event_store(self):
        """Test event store functionality."""
        print("\nTesting Event Store...")
        
        try:
            # Create event store
            self.event_store = get_event_store()
            self.log_test("Event Store Creation", True)
            
            # Test event storage
            execution_id = str(uuid.uuid4())
            test_events = [
                ExecutionEvent(
                    event_type=EventType.EXECUTION_STARTED,
                    execution_id=execution_id,
                    timestamp=datetime.now(timezone.utc),
                    data={"step": i},
                )
                for i in range(3)
            ]
            
            # Store events
            for event in test_events:
                await self.event_store.store_event(event)
            
            self.log_test("Event Storage", True, f"Stored {len(test_events)} events")
            
            # Test event retrieval
            retrieved_events = await self.event_store.get_events(execution_id)
            if len(retrieved_events) == 3:
                self.log_test("Event Retrieval", True, f"Retrieved {len(retrieved_events)} events")
            else:
                self.log_test("Event Retrieval", False, f"Expected 3 events, got {len(retrieved_events)}")
            
            # Test metrics
            metrics = await self.event_store.get_metrics()
            self.log_test("Event Store Metrics", True, f"Events stored: {metrics.get('events_stored', 0)}")
            
        except Exception as e:
            self.log_test("Event Store", False, str(e))
    
    async def test_node_implementations(self):
        """Test node implementations."""
        print("\nTesting Node Implementations...")
        
        try:
            # Create node factory
            self.node_factory = NodeFactory()
            self.log_test("Node Factory Creation", True)
            
            # Test available node types
            available_types = self.node_factory.get_available_node_types()
            expected_types = [NodeType.INPUT, NodeType.OUTPUT, NodeType.LLM, NodeType.RETRIEVAL, NodeType.TOOL]
            
            missing_types = [t for t in expected_types if t not in available_types]
            if not missing_types:
                self.log_test("Node Type Registration", True, f"All {len(expected_types)} types available")
            else:
                self.log_test("Node Type Registration", False, f"Missing: {missing_types}")
            
            # Test Input Node
            # Create a simple config for the node
            from app.domain.execution.models import NodeConfiguration
            config = NodeConfiguration(node_id="test_input", node_type="input", config={})
            input_node = self.node_factory.create_node(NodeType.INPUT, "test_input", config)
            self.log_test("Input Node Creation", True)
            
            # Test Input Node execution
            input_data = NodeInput(
                data={"value": "test input data"},
                metadata={"source": "manual_test"},
            )
            
            context = NodeContext(
                node_id="test_input",
                execution_id=str(uuid.uuid4()),
                workspace_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                config=None,
            )
            
            input_output = await input_node.run(input_data, context)
            
            if input_output.error is None and input_output.data["value"] == "test input data":
                self.log_test("Input Node Execution", True, "Output: " + str(input_output.data["value"]))
            else:
                self.log_test("Input Node Execution", False, f"Error: {input_output.error}")
            
            # Test Output Node
            # Create a simple config for the node
            config = NodeConfiguration(node_id="test_output", node_type="output", config={})
            output_node = self.node_factory.create_node(NodeType.OUTPUT, "test_output", config)
            self.log_test("Output Node Creation", True)
            
            # Test Output Node execution
            output_data = NodeInput(
                data={"result": {"message": "Hello, World!", "count": 42}},
                metadata={"source": "manual_test"},
            )
            
            output_context = NodeContext(
                node_id="test_output",
                execution_id=str(uuid.uuid4()),
                workspace_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                config=None,
            )
            
            output_output = await output_node.run(output_data, output_context)
            
            if output_output.error is None and "result" in output_output.data:
                self.log_test("Output Node Execution", True, f"Output type: {output_output.data['type']}")
            else:
                self.log_test("Output Node Execution", False, f"Error: {output_output.error}")
            
        except Exception as e:
            self.log_test("Node Implementations", False, str(e))
    
    async def test_event_handlers(self):
        """Test event handlers."""
        print("\nTesting Event Handlers...")
        
        try:
            from app.events.handlers.execution_handlers import HandlerConfig
            
            # Create handler config
            handler_config = HandlerConfig(enabled=True, enable_metrics=True)
            
            # Test Execution Event Handler
            execution_handler = ExecutionEventHandler(handler_config)
            self.log_test("Execution Handler Creation", True)
            
            # Test Node Event Handler
            node_handler = NodeEventHandler(handler_config)
            self.log_test("Node Handler Creation", True)
            
            # Test Metrics Event Handler
            metrics_handler = MetricsEventHandler(handler_config)
            self.log_test("Metrics Handler Creation", True)
            
            # Test handling events
            test_event = ExecutionEvent(
                event_type=EventType.EXECUTION_STARTED,
                execution_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                data={"test": "handler_test"},
            )
            
            await execution_handler.handle_with_retry(test_event)
            await node_handler.handle_with_retry(test_event)
            await metrics_handler.handle_with_retry(test_event)
            
            # Check handler states
            exec_state = execution_handler.get_execution_state(test_event.execution_id)
            if exec_state:
                self.log_test("Execution Handler State", True, f"Status: {exec_state.get('status')}")
            else:
                self.log_test("Execution Handler State", False, "No state found")
            
            # Check metrics
            global_metrics = metrics_handler.get_global_metrics()
            self.log_test("Metrics Handler", True, f"Total executions: {global_metrics.get('total_executions', 0)}")
            
        except Exception as e:
            self.log_test("Event Handlers", False, str(e))
    
    async def test_integration(self):
        """Test integration of all components."""
        print("\nTesting System Integration...")
        
        try:
            # Create a simple execution flow
            execution_id = str(uuid.uuid4())
            
            # Start execution
            start_event = ExecutionEvent(
                event_type=EventType.EXECUTION_STARTED,
                execution_id=execution_id,
                timestamp=datetime.now(timezone.utc),
                data={"integration_test": True},
            )
            
            await self.event_bus.publish(start_event)
            await self.event_store.store_event(start_event)
            
            # Execute a simple node flow
            # Create a simple config for the node
            from app.domain.execution.models import NodeConfiguration
            config = NodeConfiguration(node_id="integration_input", node_type="input", config={})
            input_node = self.node_factory.create_node(NodeType.INPUT, "integration_input", config)
            
            context = NodeContext(
                node_id="integration_input",
                execution_id=execution_id,
                workspace_id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                config=None,
            )
            
            input_data = NodeInput(data={"value": "integration test"})
            input_output = await input_node.run(input_data, context)
            
            # Create node completion event
            node_event = ExecutionEvent(
                event_type=EventType.NODE_COMPLETED,
                execution_id=execution_id,
                node_id="integration_input",
                timestamp=datetime.now(timezone.utc),
                data={"execution_time": input_output.execution_time},
            )
            
            await self.event_bus.publish(node_event)
            await self.event_store.store_event(node_event)
            
            # Complete execution
            complete_event = ExecutionEvent(
                event_type=EventType.EXECUTION_COMPLETED,
                execution_id=execution_id,
                timestamp=datetime.now(timezone.utc),
            )
            
            await self.event_bus.publish(complete_event)
            await self.event_store.store_event(complete_event)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify results
            stored_events = await self.event_store.get_events(execution_id)
            if len(stored_events) == 3:
                self.log_test("Integration Test", True, f"Processed {len(stored_events)} events")
            else:
                self.log_test("Integration Test", False, f"Expected 3 events, got {len(stored_events)}")
            
        except Exception as e:
            self.log_test("Integration Test", False, str(e))
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = sum(1 for _, success, _ in self.test_results if not success)
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        if failed > 0:
            print("\nFailed Tests:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"  • {test_name}: {message}")
        
        print("\n" + "="*60)
        
        if failed == 0:
            print("ALL TESTS PASSED! Event system is working correctly.")
        else:
            print("Some tests failed. Please check the implementation.")
        
        print("="*60)
    
    async def run_all_tests(self):
        """Run all tests."""
        print("Starting Phase 3 Day 5 Event System Tests")
        print("="*60)
        
        await self.test_event_bus()
        await self.test_event_store()
        await self.test_node_implementations()
        await self.test_event_handlers()
        await self.test_integration()
        
        self.print_summary()


async def main():
    """Main function to run tests."""
    tester = EventSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("Phase 3 Day 5 Event System Manual Testing")
    print("=========================================")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()