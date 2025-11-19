"""
Unit tests for execution components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

from app.execution.compiler.dag_compiler import DAGCompiler
from app.execution.validation.graph_validator import GraphValidator
from app.execution.context.manager import ContextManager
from app.execution.executor.dag_executor import DAGExecutor
from app.execution.execution.resource_manager import ResourceManager, ResourceType
from app.domain.execution.models import (
    ExecutionStatus
)
from app.execution.compiler.dag_compiler import (
    DAGCompiler, NodeType, CompilationResult
)
from app.execution.validation.graph_validator import (
    GraphValidator, ValidationResult
)
from app.execution.context.manager import (
    ContextManager, ContextStatus
)
from app.events.bus import EventBus
from app.events.store import EventStore


class TestDAGCompiler:
    """Test cases for DAG Compiler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.compiler = DAGCompiler()
    
    @pytest.mark.asyncio
    async def test_compile_simple_graph(self):
        """Test compiling a simple graph."""
        # Create test graph JSON
        graph_json = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "input",
                    "data": {"message": "Hello"},
                    "position": {"x": 0, "y": 0}
                },
                {
                    "id": "node2",
                    "type": "llm",
                    "data": {"model": "gpt-4", "prompt": "{{node1.message}}"},
                    "position": {"x": 100, "y": 0}
                },
                {
                    "id": "node3",
                    "type": "output",
                    "data": {"output": "{{node2.response}}"},
                    "position": {"x": 200, "y": 0}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "node1",
                    "target": "node2",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                },
                {
                    "id": "edge2",
                    "source": "node2",
                    "target": "node3",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                }
            ]
        }
        
        # Compile graph
        compiled_graph = await self.compiler.compile_graph(graph_json)
        
        # Verify compilation
        assert compiled_graph is not None
        assert compiled_graph.is_valid is True
        assert len(compiled_graph.nodes) == 3
        assert len(compiled_graph.execution_plan) == 3
        assert compiled_graph.execution_plan[0] == ["node1"]
        assert compiled_graph.execution_plan[1] == ["node2"]
        assert compiled_graph.execution_plan[2] == ["node3"]
    
    @pytest.mark.asyncio
    async def test_compile_graph_with_cycles(self):
        """Test compiling a graph with cycles."""
        # Create graph JSON with cycle
        graph_json = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "llm",
                    "data": {"model": "gpt-4"},
                    "position": {"x": 0, "y": 0}
                },
                {
                    "id": "node2",
                    "type": "llm",
                    "data": {"model": "gpt-4"},
                    "position": {"x": 100, "y": 0}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "node1",
                    "target": "node2",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                },
                {
                    "id": "edge2",
                    "source": "node2",
                    "target": "node1",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                }
            ]
        }
        
        # Compile graph - should fail due to cycle
        compiled_graph = await self.compiler.compile_graph(graph_json)
        
        # Should be invalid due to cycle
        assert compiled_graph.is_valid is False
        assert any("cycle" in error.lower() for error in compiled_graph.errors)
    
    @pytest.mark.asyncio
    async def test_optimize_graph(self):
        """Test graph optimization."""
        # Create graph JSON with dead code
        graph_json = {
            "nodes": [
                {
                    "id": "active_node",
                    "type": "input",
                    "data": {"message": "Hello"},
                    "position": {"x": 0, "y": 0}
                },
                {
                    "id": "dead_node",
                    "type": "llm",
                    "data": {"model": "gpt-4"},
                    "position": {"x": 100, "y": 100}
                }
            ],
            "edges": []  # No edges to dead_node
        }
        
        # Compile graph - should optimize dead code
        compiled_graph = await self.compiler.compile_graph(graph_json)
        
        # Should be valid and optimized
        assert compiled_graph.is_valid is True
        # Dead code elimination should remove the dead node
        assert len(compiled_graph.nodes) == 1
        assert compiled_graph.nodes[0].id == "active_node"
        assert "dead_code_elimination" in compiled_graph.optimization_applied


class TestGraphValidator:
    """Test cases for Graph Validator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = GraphValidator()
    
    @pytest.mark.asyncio
    async def test_validate_valid_graph(self):
        """Test validating a valid graph."""
        # Create valid graph JSON
        graph_json = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "input",
                    "data": {"message": "Hello"},
                    "position": {"x": 0, "y": 0}
                },
                {
                    "id": "node2",
                    "type": "output",
                    "data": {"output": "{{node1.message}}"},
                    "position": {"x": 100, "y": 0}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "node1",
                    "target": "node2",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                }
            ]
        }
        
        result = await self.validator.validate_graph(graph_json)
        
        # Should be valid
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_graph_with_missing_input(self):
        """Test validating graph with missing input node."""
        graph_json = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "llm",
                    "data": {"model": "gpt-4"},
                    "position": {"x": 0, "y": 0}
                }
            ],
            "edges": []
        }
        
        result = await self.validator.validate_graph(graph_json)
        
        # Should be invalid
        assert result.is_valid is False
        assert any("input" in error.message.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_graph_with_missing_output(self):
        """Test validating graph with missing output node."""
        graph_json = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "input",
                    "data": {"message": "Hello"},
                    "position": {"x": 0, "y": 0}
                }
            ],
            "edges": []
        }
        
        result = await self.validator.validate_graph(graph_json)
        
        # Should be invalid
        assert result.is_valid is False
        assert any("output" in error.message.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_graph_with_invalid_edges(self):
        """Test validating graph with invalid edges."""
        graph_json = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "input",
                    "data": {"message": "Hello"},
                    "position": {"x": 0, "y": 0}
                },
                {
                    "id": "node2",
                    "type": "output",
                    "data": {"output": "{{node1.message}}"},
                    "position": {"x": 100, "y": 0}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "nonexistent_node",
                    "target": "node2",
                    "sourceHandle": "output",
                    "targetHandle": "input"
                }
            ]
        }
        
        result = await self.validator.validate_graph(graph_json)
        
        # Should be invalid
        assert result.is_valid is False
        assert any("edge" in error.message.lower() or "does not exist" in error.message.lower() for error in result.errors)


class TestContextManager:
    """Test cases for Execution Context Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context_manager = ContextManager()
    
    @pytest.mark.asyncio
    async def test_create_context(self):
        """Test creating execution context."""
        execution_id = "test_execution_123"
        
        # Create context using async context manager
        async with self.context_manager.create_context(
            execution_id=execution_id,
            workspace_id="test_workspace",
            user_id="test_user",
            agent_id="test_agent"
        ) as context:
            # Verify context creation
            assert context.execution_id == execution_id
            assert context.status.value == "ready"  # Should be ready after initialization
            assert context.workspace_id == "test_workspace"
            assert context.user_id == "test_user"
            assert context.agent_id == "test_agent"
            assert context.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_context(self):
        """Test getting execution context."""
        execution_id = "test_execution_123"
        
        # Create context
        async with self.context_manager.create_context(
            execution_id=execution_id,
            workspace_id="test_workspace",
            user_id="test_user",
            agent_id="test_agent"
        ) as created_context:
            # Get context
            retrieved_context = await self.context_manager.get_context(execution_id)
            
            # Should be the same context
            assert retrieved_context.execution_id == created_context.execution_id
            assert retrieved_context.status == created_context.status
    
    @pytest.mark.asyncio
    async def test_update_context_status(self):
        """Test updating execution context status."""
        execution_id = "test_execution_123"
        
        # Create context
        async with self.context_manager.create_context(
            execution_id=execution_id,
            workspace_id="test_workspace",
            user_id="test_user",
            agent_id="test_agent"
        ) as context:
            # Update context status
            from app.execution.context.manager import ContextStatus
            await self.context_manager.update_context_status(execution_id, ContextStatus.RUNNING)
            
            # Verify update
            updated_context = await self.context_manager.get_context(execution_id)
            assert updated_context.status == ContextStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_cleanup_context(self):
        """Test cleaning up execution context."""
        execution_id = "test_execution_123"
        
        # Create context
        async with self.context_manager.create_context(
            execution_id=execution_id,
            workspace_id="test_workspace",
            user_id="test_user",
            agent_id="test_agent"
        ) as context:
            pass  # Context is automatically cleaned up when exiting
        
        # Should be cleaned up (no longer active)
        retrieved_context = await self.context_manager.get_context(execution_id)
        assert retrieved_context is not None  # Still exists but not active
        assert execution_id not in self.context_manager.get_active_contexts()
    
    @pytest.mark.asyncio
    async def test_context_metrics(self):
        """Test context manager metrics."""
        execution_id = "test_execution_123"
        
        # Create context
        async with self.context_manager.create_context(
            execution_id=execution_id,
            workspace_id="test_workspace",
            user_id="test_user",
            agent_id="test_agent"
        ) as context:
            pass
        
        # Check metrics
        metrics = self.context_manager.get_metrics()
        assert metrics["contexts_created"] >= 1
        assert "contexts_completed" in metrics
        assert "contexts_failed" in metrics
        assert "average_execution_time" in metrics


class TestResourceManager:
    """Test cases for Resource Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resource_manager = ResourceManager()
    
    @pytest.mark.asyncio
    async def test_allocate_resources(self):
        """Test resource allocation."""
        execution_id = "test_execution_123"
        resource_requirements = {
            "cpu_per_node": 0.1,
            "memory_per_node": 100.0,
            "network_connections": 1
        }
        
        # Allocate resources using async context manager
        async with self.resource_manager.allocate_resources(
            execution_id=execution_id,
            estimated_duration=30.0,
            node_count=1,
            resource_requirements=resource_requirements
        ) as allocation:
            # Verify allocation
            assert allocation.execution_id == execution_id
            assert allocation.status == "active"
            assert ResourceType.CPU in allocation.allocated_resources
            assert ResourceType.MEMORY in allocation.allocated_resources
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """Test resource cleanup after allocation."""
        execution_id = "test_execution_123"
        resource_requirements = {
            "cpu_per_node": 0.1,
            "memory_per_node": 100.0
        }
        
        # Allocate resources
        async with self.resource_manager.allocate_resources(
            execution_id=execution_id,
            estimated_duration=30.0,
            node_count=1,
            resource_requirements=resource_requirements
        ) as allocation:
            assert allocation.execution_id == execution_id
        
        # Should be cleaned up after context manager exits
        retrieved_allocation = self.resource_manager._get_allocation(execution_id)
        assert retrieved_allocation is None
    
    def test_get_resource_usage(self):
        """Test getting resource usage."""
        execution_id = "test_execution_123"
        
        # Get resource usage without allocation
        usage = self.resource_manager.get_resource_usage(execution_id)
        
        # Verify usage structure
        assert "current_usage" in usage
        assert "resource_limits" in usage
        assert "system_info" in usage
        assert ResourceType.CPU.value in usage["current_usage"]
        assert ResourceType.MEMORY.value in usage["current_usage"]
    
    def test_get_available_resources(self):
        """Test getting available resources."""
        # Get available resources
        available = self.resource_manager.get_available_resources()
        
        # Verify available resources structure
        assert "available_resources" in available
        assert "current_usage" in available
        assert "resource_limits" in available
        assert "system_info" in available
        
        # Check that available resources are calculated
        available_resources = available["available_resources"]
        assert f"max_{ResourceType.CPU.value}_usage" in available_resources
        assert f"max_{ResourceType.MEMORY.value}_usage" in available_resources
    
    def test_get_metrics(self):
        """Test getting resource manager metrics."""
        # Get metrics
        metrics = self.resource_manager.get_metrics()
        
        # Verify metrics structure
        assert "allocations_created" in metrics
        assert "allocations_completed" in metrics
        assert "allocations_failed" in metrics
        assert "resource_violations" in metrics
        assert "auto_scaling_events" in metrics
        assert "total_monitoring_time" in metrics
        assert "peak_cpu_usage" in metrics
        assert "peak_memory_usage" in metrics


class TestDAGExecutor:
    """Test cases for DAG Executor."""
    
    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create mock context manager."""
        return Mock(spec=ExecutionContextManager)
    
    @pytest.fixture
    def mock_resource_manager(self):
        """Create mock resource manager."""
        return Mock(spec=ResourceManager)
    
    def setup_method(self):
        """Set up test fixtures."""
        self.executor = DAGExecutor()
    
    @pytest.mark.asyncio
    async def test_execute_simple_graph(self, mock_event_bus, mock_context_manager, mock_resource_manager):
        """Test executing a simple graph."""
        # Create test graph
        nodes = [
            ExecutionNode(
                id="node1",
                type=NodeType.INPUT,
                config={"data": {"message": "Hello"}},
                position={"x": 0, "y": 0}
            ),
            ExecutionNode(
                id="node2",
                type=NodeType.OUTPUT,
                config={"output": "{{node1.message}}"},
                position={"x": 100, "y": 0}
            )
        ]
        
        edges = [
            ExecutionEdge(
                id="edge1",
                source="node1",
                target="node2",
                source_handle="output",
                target_handle="input"
            )
        ]
        
        graph = ExecutionGraph(nodes=nodes, edges=edges)
        
        # Mock dependencies
        mock_context = Mock()
        mock_context.execution_id = "test_execution_123"
        mock_context_manager.create_context.return_value = mock_context
        mock_context_manager.get_context.return_value = mock_context
        
        mock_allocation = Mock()
        mock_resource_manager.allocate_resources.return_value = mock_allocation
        
        # Execute graph
        result = await self.executor.execute(
            graph=graph,
            context_manager=mock_context_manager,
            resource_manager=mock_resource_manager,
            event_bus=mock_event_bus
        )
        
        # Verify execution
        assert result.execution_id == "test_execution_123"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output_data is not None
    
    @pytest.mark.asyncio
    async def test_execute_graph_with_error(self, mock_event_bus, mock_context_manager, mock_resource_manager):
        """Test executing graph with error."""
        # Create invalid graph
        nodes = [
            ExecutionNode(
                id="node1",
                type=NodeType.LLM,
                config={"model": "invalid_model"},
                position={"x": 0, "y": 0}
            )
        ]
        
        edges = []
        
        graph = ExecutionGraph(nodes=nodes, edges=edges)
        
        # Mock dependencies
        mock_context = Mock()
        mock_context.execution_id = "test_execution_123"
        mock_context_manager.create_context.return_value = mock_context
        mock_context_manager.get_context.return_value = mock_context
        
        mock_allocation = Mock()
        mock_resource_manager.allocate_resources.return_value = mock_allocation
        
        # Execute graph - should handle error
        result = await self.executor.execute(
            graph=graph,
            context_manager=mock_context_manager,
            resource_manager=mock_resource_manager,
            event_bus=mock_event_bus
        )
        
        # Verify error handling
        assert result.execution_id == "test_execution_123"
        assert result.status == ExecutionStatus.FAILED
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, mock_event_bus, mock_context_manager, mock_resource_manager):
        """Test cancelling execution."""
        execution_id = "test_execution_123"
        
        # Mock context
        mock_context = Mock()
        mock_context.execution_id = execution_id
        mock_context.status = ExecutionStatus.RUNNING
        mock_context_manager.get_context.return_value = mock_context
        
        # Cancel execution
        cancelled = await self.executor.cancel_execution(
            execution_id,
            context_manager=mock_context_manager,
            event_bus=mock_event_bus
        )
        
        # Verify cancellation
        assert cancelled is True
        assert mock_context.status == ExecutionStatus.CANCELLED


if __name__ == "__main__":
    pytest.main([__file__])