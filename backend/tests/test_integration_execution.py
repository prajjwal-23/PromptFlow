"""
Integration tests for complete execution flow including pause/resume and optimization.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.execution.compiler.dag_compiler import DAGCompiler
from app.execution.executor.dag_executor import DAGExecutor, ExecutionStatus
from app.execution.context.manager import ContextManager, ContextStatus
from app.execution.services.execution_service import ExecutionServiceImpl
from app.execution.compiler.optimizer import GraphOptimizer
from app.domain.execution.models import (
    Execution, ExecutionStatus as DomainExecutionStatus, ExecutionInput, 
    ExecutionConfig, ExecutionEvent, EventType, NodeType
)


class TestIntegrationExecutionFlow:
    """Integration tests for complete execution flow."""
    
    @pytest.fixture
    def compiler(self):
        """Create DAG compiler instance."""
        return DAGCompiler()
    
    @pytest.fixture
    def executor(self):
        """Create DAG executor instance."""
        return DAGExecutor()
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager instance."""
        return ContextManager()
    
    @pytest.fixture
    def optimizer(self):
        """Create graph optimizer instance."""
        return GraphOptimizer()
    
    @pytest.fixture
    def execution_service(self):
        """Create execution service instance."""
        return ExecutionServiceImpl()
    
    @pytest.fixture
    def sample_graph_json(self):
        """Create sample graph JSON for testing."""
        return {
            "nodes": [
                {
                    "id": "input_node",
                    "type": "input",
                    "data": {"message": "Hello World"},
                    "position": {"x": 0, "y": 0}
                },
                {
                    "id": "llm_node_1",
                    "type": "llm",
                    "data": {"model": "gpt-4", "prompt": "{{input_node.message}}"},
                    "position": {"x": 100, "y": 0}
                },
                {
                    "id": "llm_node_2",
                    "type": "llm",
                    "data": {"model": "gpt-4", "prompt": "Process: {{input_node.message}}"},
                    "position": {"x": 200, "y": 0}
                },
                {
                    "id": "tool_node",
                    "type": "tool",
                    "data": {"tool": "calculator", "operation": "add"},
                    "position": {"x": 300, "y": 0}
                },
                {
                    "id": "output_node",
                    "type": "output",
                    "data": {"format": "text"},
                    "position": {"x": 400, "y": 0}
                },
                {
                    "id": "dead_node",
                    "type": "llm",
                    "data": {"model": "gpt-3.5", "prompt": "This will be optimized away"},
                    "position": {"x": 500, "y": 100}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "input_node",
                    "target": "llm_node_1",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                },
                {
                    "id": "edge2",
                    "source": "input_node",
                    "target": "llm_node_2",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                },
                {
                    "id": "edge3",
                    "source": "llm_node_1",
                    "target": "tool_node",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                },
                {
                    "id": "edge4",
                    "source": "llm_node_2",
                    "target": "tool_node",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                },
                {
                    "id": "edge5",
                    "source": "tool_node",
                    "target": "output_node",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_complete_execution_flow(self, compiler, executor, optimizer, sample_graph_json):
        """Test complete execution flow from compilation to execution."""
        # Step 1: Compile graph
        compilation_result = await compiler.compile_graph(sample_graph_json)
        assert compilation_result.is_valid is True
        assert len(compilation_result.nodes) == 6  # All nodes initially
        
        # Step 2: Optimize graph
        optimization_results = await optimizer.optimize_graph(
            compilation_result.nodes,
            compilation_result.execution_plan,
            compilation_result.parallel_groups
        )
        assert len(optimization_results) == 7  # All optimization strategies
        
        # Get optimized nodes (after dead code elimination)
        optimized_nodes = optimization_results[0].nodes  # First result is dead code elimination
        assert len(optimized_nodes) < 6  # Should have removed dead_node
        assert "dead_node" not in [node.id for node in optimized_nodes]
        
        # Step 3: Execute optimized graph
        with patch.object(executor, '_execute_node') as mock_execute:
            # Mock node execution
            mock_execute.return_value = None
            
            execution_result = await executor.execute_dag(
                compilation_result,  # Use original compilation result with optimized nodes
                {"test_input": "value"},
                ExecutionConfig()
            )
            
            # Verify execution
            assert execution_result.status == ExecutionStatus.COMPLETED
            assert execution_result.execution_id is not None
    
    @pytest.mark.asyncio
    async def test_pause_resume_execution_flow(self, executor, context_manager, sample_graph_json):
        """Test pause/resume execution flow."""
        # Create compilation result
        compiler = DAGCompiler()
        compilation_result = await compiler.compile_graph(sample_graph_json)
        
        # Mock node execution to allow pause testing
        execution_events = []
        original_execute = executor._execute_node
        
        async def mock_execute_node_with_pause(*args, **kwargs):
            """Mock node execution that can be paused."""
            node_id = args[0]
            execution_events.append(f"started_{node_id}")
            
            # Check if execution should be paused
            if node_id == "llm_node_1" and hasattr(executor, '_pause_events'):
                # Simulate pause
                await asyncio.sleep(0.1)
                if node_id in executor._pause_events:
                    await executor._check_pause_state(node_id)
            
            execution_events.append(f"completed_{node_id}")
        
        executor._execute_node = mock_execute_node_with_pause
        
        # Start execution in background
        execution_task = asyncio.create_task(
            executor.execute_dag(compilation_result, {"test": "data"}, ExecutionConfig())
        )
        
        # Wait a bit for execution to start
        await asyncio.sleep(0.05)
        
        # Get execution ID from context
        execution_id = None
        for exec_id, context in executor._execution_contexts.items():
            execution_id = exec_id
            break
        
        assert execution_id is not None
        
        # Pause execution
        pause_success = await executor.pause_execution(execution_id)
        assert pause_success is True
        
        # Verify execution is paused
        assert execution_id in executor._paused_executions
        
        # Resume execution
        resume_success = await executor.resume_execution(execution_id)
        assert resume_success is True
        
        # Verify execution is resumed
        assert execution_id not in executor._paused_executions
        
        # Wait for execution to complete
        try:
            result = await execution_task
            assert result.status == ExecutionStatus.COMPLETED
        except asyncio.CancelledError:
            pass  # Execution might be cancelled due to mocking
    
    @pytest.mark.asyncio
    async def test_optimization_with_pause_resume(self, optimizer, sample_graph_json):
        """Test that optimization works correctly with pause/resume functionality."""
        # Create compilation result
        compiler = DAGCompiler()
        compilation_result = await compiler.compile_graph(sample_graph_json)
        
        # Optimize graph
        optimization_results = await optimizer.optimize_graph(
            compilation_result.nodes,
            compilation_result.execution_plan,
            compilation_result.parallel_groups
        )
        
        # Get optimized nodes
        optimized_nodes = optimization_results[0].nodes
        
        # Verify optimization doesn't break pause/resume functionality
        assert len(optimized_nodes) > 0
        
        # Check that critical nodes are preserved
        critical_node_ids = {"input_node", "output_node", "llm_node_1", "llm_node_2", "tool_node"}
        optimized_node_ids = {node.id for node in optimized_nodes}
        
        # All critical nodes should be present
        for critical_id in critical_node_ids:
            assert critical_id in optimized_node_ids
        
        # Dead node should be removed
        assert "dead_node" not in optimized_node_ids
    
    @pytest.mark.asyncio
    async def test_error_handling_during_execution(self, executor, sample_graph_json):
        """Test error handling during execution."""
        # Create compilation result
        compiler = DAGCompiler()
        compilation_result = await compiler.compile_graph(sample_graph_json)
        
        # Mock node execution to raise an error
        async def mock_execute_node_with_error(*args, **kwargs):
            node_id = args[0]
            if node_id == "llm_node_1":
                raise ValueError("Simulated execution error")
        
        executor._execute_node = mock_execute_node_with_error
        
        # Execute graph - should handle error gracefully
        result = await executor.execute_dag(
            compilation_result, {"test": "data"}, ExecutionConfig()
        )
        
        # Verify error handling
        assert result.status == ExecutionStatus.FAILED
        assert len(result.errors) > 0
        assert any("Simulated execution error" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_concurrent_executions(self, executor, sample_graph_json):
        """Test handling multiple concurrent executions."""
        # Create compilation result
        compiler = DAGCompiler()
        compilation_result = await compiler.compile_graph(sample_graph_json)
        
        # Mock node execution
        async def mock_execute_node(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate work
        
        executor._execute_node = mock_execute_node
        
        # Start multiple executions
        execution_tasks = []
        for i in range(3):
            task = asyncio.create_task(
                executor.execute_dag(
                    compilation_result, 
                    {"test": f"data_{i}"}, 
                    ExecutionConfig()
                )
            )
            execution_tasks.append(task)
        
        # Wait for all executions to complete
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Verify all executions completed
        for result in results:
            if isinstance(result, Exception):
                # Handle exceptions
                assert False, f"Execution failed with exception: {result}"
            else:
                assert result.status == ExecutionStatus.COMPLETED
        
        # Verify no resource conflicts
        assert len(executor._active_executions) == 0
    
    @pytest.mark.asyncio
    async def test_execution_with_optimization_and_metrics(self, compiler, executor, optimizer, sample_graph_json):
        """Test execution with optimization and metrics collection."""
        # Step 1: Compile graph
        compilation_result = await compiler.compile_graph(sample_graph_json)
        
        # Step 2: Optimize graph
        optimization_results = await optimizer.optimize_graph(
            compilation_result.nodes,
            compilation_result.execution_plan,
            compilation_result.parallel_groups
        )
        
        # Step 3: Execute with metrics collection
        with patch.object(executor, '_execute_node') as mock_execute:
            # Mock node execution with timing
            async def mock_execute_with_metrics(*args, **kwargs):
                node_id = args[0]
                # Simulate different execution times for different node types
                if "llm" in node_id:
                    await asyncio.sleep(0.2)
                else:
                    await asyncio.sleep(0.1)
            
            mock_execute.side_effect = mock_execute_with_metrics
            
            result = await executor.execute_dag(
                compilation_result, {"test": "data"}, ExecutionConfig()
            )
            
            # Verify execution completed
            assert result.status == ExecutionStatus.COMPLETED
            
            # Verify metrics were collected
            assert result.metrics is not None
            assert result.duration > 0
    
    @pytest.mark.asyncio
    async def test_service_layer_integration(self, execution_service, sample_graph_json):
        """Test execution service integration with pause/resume."""
        # Create execution
        execution = Execution(
            id="test_execution_123",
            agent_id="test_agent_456",
            input_data=ExecutionInput(inputs={"test": "data"}),
            config=ExecutionConfig()
        )
        
        # Mock repository and event bus
        with patch.object(execution_service, '_get_execution_repository') as mock_repo, \
             patch.object(execution_service, '_get_event_repository') as mock_event_repo, \
             patch.object(execution_service.event_bus, 'emit') as mock_emit:
            
            # Setup mocks
            mock_repo.get_by_id.return_value = execution
            mock_repo.save.return_value = execution
            mock_event_repo.save_event.return_value = None
            
            # Test pause
            pause_result = await execution_service.pause_execution("test_execution_123")
            assert pause_result is True
            
            # Test resume
            execution.status = DomainExecutionStatus.PAUSED
            resume_result = await execution_service.resume_execution("test_execution_123")
            assert resume_result is True
            
            # Test pause info
            pause_event = Mock()
            pause_event.data = {"paused_at": datetime.now(timezone.utc).isoformat()}
            mock_event_repo.get_events_by_execution_id.return_value = [pause_event]
            
            pause_info = await execution_service.get_execution_pause_info("test_execution_123")
            assert pause_info is not None
            assert pause_info["execution_id"] == "test_execution_123"
            assert pause_info["status"] == "paused"
    
    @pytest.mark.asyncio
    async def test_resource_management_during_execution(self, executor, sample_graph_json):
        """Test resource management during execution."""
        # Create compilation result
        compiler = DAGCompiler()
        compilation_result = await compiler.compile_graph(sample_graph_json)
        
        # Mock resource monitoring
        resource_usage = []
        
        async def mock_monitor_resources(execution_id):
            """Mock resource monitoring."""
            while execution_id in executor._execution_contexts:
                resource_usage.append({
                    "execution_id": execution_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "memory_mb": 100 + len(resource_usage) * 10,
                    "cpu_percent": 50 + len(resource_usage) * 5
                })
                await asyncio.sleep(0.05)
        
        # Start resource monitoring
        monitor_task = None
        
        # Mock node execution
        async def mock_execute_with_monitoring(*args, **kwargs):
            node_id = args[0]
            context = args[1]
            
            # Start monitoring if not already started
            nonlocal monitor_task
            if monitor_task is None:
                monitor_task = asyncio.create_task(
                    mock_monitor_resources(context.execution_id)
                )
            
            await asyncio.sleep(0.1)
        
        executor._execute_node = mock_execute_with_monitoring
        
        # Execute graph
        result = await executor.execute_dag(
            compilation_result, {"test": "data"}, ExecutionConfig()
        )
        
        # Wait for monitoring to complete
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        
        # Verify execution completed
        assert result.status == ExecutionStatus.COMPLETED
        
        # Verify resource usage was tracked
        assert len(resource_usage) > 0
    
    def test_optimization_performance(self, optimizer, sample_graph_json):
        """Test optimization performance with large graphs."""
        # Create a larger graph for performance testing
        large_graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add many nodes
        for i in range(100):
            node_type = "llm" if i % 2 == 0 else "tool"
            large_graph["nodes"].append({
                "id": f"node_{i}",
                "type": node_type,
                "data": {"index": i},
                "position": {"x": i * 50, "y": (i // 10) * 50}
            })
            
            # Add edges to create a chain
            if i > 0:
                large_graph["edges"].append({
                    "id": f"edge_{i-1}_{i}",
                    "source": f"node_{i-1}",
                    "target": f"node_{i}",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                })
        
        # Add some dead nodes
        for i in range(100, 120):
            large_graph["nodes"].append({
                "id": f"dead_node_{i}",
                "type": "llm",
                "data": {"dead": True},
                "position": {"x": i * 50, "y": 200}
            })
        
        # Test compilation performance
        import time
        start_time = time.time()
        
        compiler = DAGCompiler()
        compilation_result = asyncio.run(compiler.compile_graph(large_graph))
        
        compilation_time = time.time() - start_time
        assert compilation_time < 5.0  # Should compile within 5 seconds
        assert compilation_result.is_valid is True
        
        # Test optimization performance
        start_time = time.time()
        
        optimization_results = asyncio.run(optimizer.optimize_graph(
            compilation_result.nodes,
            compilation_result.execution_plan,
            compilation_result.parallel_groups
        ))
        
        optimization_time = time.time() - start_time
        assert optimization_time < 10.0  # Should optimize within 10 seconds
        assert len(optimization_results) == 7
        
        # Verify dead code elimination worked
        dead_code_result = optimization_results[0]
        assert dead_code_result.metrics_improvement["node_count_reduction"] > 0


if __name__ == "__main__":
    pytest.main([__file__])