"""
Comprehensive tests for graph optimizer functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.execution.compiler.optimizer import (
    GraphOptimizer, OptimizationType, OptimizationResult, 
    ResourcePrediction, CostAnalysis
)
from app.domain.execution.models import (
    CompiledNode, NodeType, NodeConfiguration, ExecutionConfig
)


class TestGraphOptimizer:
    """Test cases for graph optimizer functionality."""
    
    @pytest.fixture
    def optimizer(self):
        """Create graph optimizer instance."""
        return GraphOptimizer()
    
    @pytest.fixture
    def sample_nodes(self):
        """Create sample compiled nodes for testing."""
        return [
            CompiledNode(
                id="input_node",
                type=NodeType.INPUT,
                config=NodeConfiguration(
                    node_id="input_node",
                    node_type="input",
                    config={"data": {"message": "Hello"}}
                ),
                dependencies=[],
                execution_order=0
            ),
            CompiledNode(
                id="llm_node_1",
                type=NodeType.LLM,
                config=NodeConfiguration(
                    node_id="llm_node_1",
                    node_type="llm",
                    config={"model": "gpt-4", "prompt": "Hello world"}
                ),
                dependencies=["input_node"],
                execution_order=1
            ),
            CompiledNode(
                id="llm_node_2",
                type=NodeType.LLM,
                config=NodeConfiguration(
                    node_id="llm_node_2",
                    node_type="llm",
                    config={"model": "gpt-4", "prompt": "Another prompt"}
                ),
                dependencies=["input_node"],
                execution_order=1
            ),
            CompiledNode(
                id="output_node",
                type=NodeType.OUTPUT,
                config=NodeConfiguration(
                    node_id="output_node",
                    node_type="output",
                    config={"format": "text"}
                ),
                dependencies=["llm_node_1", "llm_node_2"],
                execution_order=2
            ),
            CompiledNode(
                id="dead_node",
                type=NodeType.LLM,
                config=NodeConfiguration(
                    node_id="dead_node",
                    node_type="llm",
                    config={"model": "gpt-3.5", "prompt": "Dead code"}
                ),
                dependencies=[],
                execution_order=1
            )
        ]
    
    @pytest.fixture
    def execution_plan(self):
        """Create sample execution plan."""
        return [
            ["input_node"],
            ["llm_node_1", "llm_node_2", "dead_node"],
            ["output_node"]
        ]
    
    @pytest.fixture
    def parallel_groups(self):
        """Create sample parallel groups."""
        return [
            ["input_node"],
            ["llm_node_1", "llm_node_2"],
            ["output_node"]
        ]
    
    @pytest.mark.asyncio
    async def test_optimize_graph_comprehensive(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test comprehensive graph optimization."""
        # Run full optimization
        results = await optimizer.optimize_graph(
            sample_nodes, execution_plan, parallel_groups
        )
        
        # Verify all optimization types were applied
        assert len(results) == 7  # 7 optimization strategies
        
        optimization_types = [result.optimization_type for result in results]
        expected_types = [
            OptimizationType.DEAD_CODE_ELIMINATION,
            OptimizationType.NODE_MERGING,
            OptimizationType.PARALLEL_EXECUTION,
            OptimizationType.RESOURCE_OPTIMIZATION,
            OptimizationType.COST_BASED_OPTIMIZATION,
            OptimizationType.CACHING_OPTIMIZATION,
            OptimizationType.EDGE_OPTIMIZATION
        ]
        
        for expected_type in expected_types:
            assert expected_type in optimization_types
        
        # Verify dead code elimination worked
        dead_code_result = next(r for r in results if r.optimization_type == OptimizationType.DEAD_CODE_ELIMINATION)
        assert dead_code_result.success
        assert "dead_node" not in [node.id for node in dead_code_result.nodes]
        assert dead_code_result.metrics_improvement["node_count_reduction"] > 0
    
    @pytest.mark.asyncio
    async def test_eliminate_dead_code(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test dead code elimination optimization."""
        result = await optimizer.eliminate_dead_code(sample_nodes, execution_plan, parallel_groups)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.DEAD_CODE_ELIMINATION
        assert result.success is True
        
        # Verify dead node was removed
        remaining_node_ids = [node.id for node in result.nodes]
        assert "dead_node" not in remaining_node_ids
        assert "input_node" in remaining_node_ids
        assert "output_node" in remaining_node_ids
        
        # Verify execution plan was updated
        for level in result.execution_plan:
            assert "dead_node" not in level
        
        # Verify metrics improvement
        assert result.metrics_improvement["node_count_reduction"] > 0
        assert "eliminated_nodes" in result.metadata
        assert "dead_node" in result.metadata["eliminated_nodes"]
    
    @pytest.mark.asyncio
    async def test_merge_compatible_nodes(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test node merging optimization."""
        result = await optimizer.merge_compatible_nodes(sample_nodes, execution_plan, parallel_groups)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.NODE_MERGING
        assert result.success is True
        
        # Check if LLM nodes were merged (they have same type and execution order)
        llm_nodes = [node for node in result.nodes if node.type == NodeType.LLM]
        
        # Should have fewer nodes after merging
        original_llm_count = len([n for n in sample_nodes if n.type == NodeType.LLM])
        assert len(llm_nodes) <= original_llm_count
        
        # Verify metrics improvement
        if result.metrics_improvement["node_count_reduction"] > 0:
            assert "merge_operations" in result.metadata
            assert len(result.metadata["merge_operations"]) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_parallel_execution(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test parallel execution optimization."""
        result = await optimizer.optimize_parallel_execution(sample_nodes, execution_plan, parallel_groups)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.PARALLEL_EXECUTION
        assert result.success is True
        
        # Verify parallel groups were optimized
        assert len(result.parallel_groups) > 0
        
        # Verify metrics improvement
        assert "parallelism_improvement" in result.metrics_improvement
        assert "critical_path_length" in result.metrics_improvement
        assert "critical_path" in result.metadata
    
    @pytest.mark.asyncio
    async def test_optimize_resource_usage(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test resource usage optimization."""
        config = ExecutionConfig(max_execution_time=300)
        result = await optimizer.optimize_resource_usage(sample_nodes, execution_plan, parallel_groups, config)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.RESOURCE_OPTIMIZATION
        assert result.success is True
        
        # Verify metrics improvement
        assert "memory_improvement_percent" in result.metrics_improvement
        assert "cpu_improvement_percent" in result.metrics_improvement
        assert "time_improvement_percent" in result.metrics_improvement
        assert "optimization_time" in result.metrics_improvement
        
        # Verify metadata
        assert "original_prediction" in result.metadata
        assert "optimized_prediction" in result.metadata
        assert "optimizations_applied" in result.metadata
    
    @pytest.mark.asyncio
    async def test_optimize_for_cost(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test cost-based optimization."""
        config = ExecutionConfig()
        result = await optimizer.optimize_for_cost(sample_nodes, execution_plan, parallel_groups, config)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.COST_BASED_OPTIMIZATION
        assert result.success is True
        
        # Verify metrics improvement
        assert "cost_savings_percent" in result.metrics_improvement
        assert "cost_savings_amount" in result.metrics_improvement
        assert "optimization_time" in result.metrics_improvement
        
        # Verify metadata
        assert "original_cost_analysis" in result.metadata
        assert "optimized_cost_analysis" in result.metadata
        assert "optimizations_applied" in result.metadata
    
    @pytest.mark.asyncio
    async def test_optimize_caching(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test caching optimization."""
        result = await optimizer.optimize_caching(sample_nodes, execution_plan, parallel_groups)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.CACHING_OPTIMIZATION
        assert result.success is True
        
        # Verify metrics improvement
        assert "caching_coverage_percent" in result.metrics_improvement
        assert "nodes_with_caching" in result.metrics_improvement
        assert "optimization_time" in result.metrics_improvement
        
        # Verify metadata
        assert "caching_strategies" in result.metadata
        assert "caching_coverage" in result.metadata
        
        # Check that nodes have caching metadata
        for node in result.nodes:
            if node.metadata and "caching_strategy" in node.metadata:
                assert node.metadata["caching_strategy"] in [
                    "response_caching", "vector_caching", "result_caching"
                ]
    
    @pytest.mark.asyncio
    async def test_optimize_edges(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test edge optimization."""
        result = await optimizer.optimize_edges(sample_nodes, execution_plan, parallel_groups)
        
        # Verify optimization result
        assert isinstance(result, OptimizationResult)
        assert result.optimization_type == OptimizationType.EDGE_OPTIMIZATION
        assert result.success is True
        
        # Verify metrics improvement
        assert "edge_reduction_percent" in result.metrics_improvement
        assert "edges_removed" in result.metrics_improvement
        assert "optimization_time" in result.metrics_improvement
        
        # Verify metadata
        assert "original_edge_count" in result.metadata
        assert "optimized_edge_count" in result.metadata
        assert "edge_analysis" in result.metadata
    
    @pytest.mark.asyncio
    async def test_predict_resource_usage(self, optimizer, sample_nodes):
        """Test resource usage prediction."""
        prediction = await optimizer.predict_resource_usage(sample_nodes, [])
        
        # Verify prediction structure
        assert isinstance(prediction, ResourcePrediction)
        assert prediction.estimated_memory_mb > 0
        assert prediction.estimated_cpu_percent > 0
        assert prediction.estimated_duration_seconds > 0
        assert prediction.estimated_tokens >= 0
        assert 0 <= prediction.confidence_score <= 1
        assert "resource_requirements" in prediction.resource_requirements
    
    @pytest.mark.asyncio
    async def test_analyze_execution_cost(self, optimizer, sample_nodes):
        """Test execution cost analysis."""
        cost_analysis = await optimizer.analyze_execution_cost(sample_nodes)
        
        # Verify cost analysis structure
        assert isinstance(cost_analysis, CostAnalysis)
        assert cost_analysis.estimated_cost >= 0
        assert isinstance(cost_analysis.cost_breakdown, dict)
        assert cost_analysis.optimization_savings >= 0
        assert isinstance(cost_analysis.cost_per_node, dict)
        
        # Verify cost per node for all nodes
        for node in sample_nodes:
            assert node.id in cost_analysis.cost_per_node
            assert cost_analysis.cost_per_node[node.id] >= 0
    
    def test_calculate_merge_compatibility(self, optimizer):
        """Test node merge compatibility calculation."""
        # Create compatible nodes
        node1 = CompiledNode(
            id="node1",
            type=NodeType.LLM,
            config=NodeConfiguration(
                node_id="node1",
                node_type="llm",
                config={"model": "gpt-4"}
            ),
            dependencies=["input"],
            execution_order=1
        )
        
        node2 = CompiledNode(
            id="node2",
            type=NodeType.LLM,
            config=NodeConfiguration(
                node_id="node2",
                node_type="llm",
                config={"model": "gpt-4"}
            ),
            dependencies=["input"],
            execution_order=1
        )
        
        # Test compatible nodes
        compatibility = optimizer._calculate_merge_compatibility(node1, node2)
        assert compatibility > 0.7  # Should be highly compatible
        
        # Test incompatible nodes (different types)
        node3 = CompiledNode(
            id="node3",
            type=NodeType.INPUT,
            config=NodeConfiguration(
                node_id="node3",
                node_type="input",
                config={"data": "test"}
            ),
            dependencies=[],
            execution_order=0
        )
        
        compatibility = optimizer._calculate_merge_compatibility(node1, node3)
        assert compatibility == 0.0  # Should be incompatible
        
        # Test nodes with different execution orders
        node4 = CompiledNode(
            id="node4",
            type=NodeType.LLM,
            config=NodeConfiguration(
                node_id="node4",
                node_type="llm",
                config={"model": "gpt-4"}
            ),
            dependencies=["input"],
            execution_order=2
        )
        
        compatibility = optimizer._calculate_merge_compatibility(node1, node4)
        assert compatibility == 0.0  # Should be incompatible
    
    def test_create_merged_node(self, optimizer):
        """Test merged node creation."""
        node1 = CompiledNode(
            id="node1",
            type=NodeType.LLM,
            config=NodeConfiguration(
                node_id="node1",
                node_type="llm",
                config={"model": "gpt-4", "temperature": 0.7}
            ),
            dependencies=["input"],
            execution_order=1
        )
        
        node2 = CompiledNode(
            id="node2",
            type=NodeType.LLM,
            config=NodeConfiguration(
                node_id="node2",
                node_type="llm",
                config={"model": "gpt-4", "temperature": 0.8}
            ),
            dependencies=["input"],
            execution_order=1
        )
        
        merged_node = optimizer._create_merged_node(node1, node2)
        
        # Verify merged node properties
        assert merged_node.type == NodeType.LLM
        assert merged_node.execution_order == 1
        assert "merged_node1_node2" in merged_node.id
        assert set(merged_node.dependencies) == {"input"}
        
        # Verify metadata
        assert "merged_from" in merged_node.metadata
        assert merged_node.metadata["merged_from"] == ["node1", "node2"]
        assert "merge_timestamp" in merged_node.metadata
    
    def test_rebuild_execution_plan(self, optimizer):
        """Test execution plan rebuilding."""
        nodes = [
            CompiledNode("node1", NodeType.INPUT, None, [], 0),
            CompiledNode("node2", NodeType.LLM, None, ["node1"], 1),
            CompiledNode("node3", NodeType.LLM, None, ["node1"], 1),
            CompiledNode("node4", NodeType.OUTPUT, None, ["node2", "node3"], 2)
        ]
        
        plan = optimizer._rebuild_execution_plan(nodes)
        
        # Verify plan structure
        assert isinstance(plan, list)
        assert len(plan) == 3  # 3 execution levels
        
        # Verify execution order
        assert plan[0] == ["node1"]
        assert set(plan[1]) == {"node2", "node3"}
        assert plan[2] == ["node4"]
    
    def test_rebuild_parallel_groups(self, optimizer):
        """Test parallel groups rebuilding."""
        nodes = [
            CompiledNode("node1", NodeType.INPUT, None, [], 0),
            CompiledNode("node2", NodeType.LLM, None, ["node1"], 1),
            CompiledNode("node3", NodeType.LLM, None, ["node1"], 1),
            CompiledNode("node4", NodeType.OUTPUT, None, ["node2", "node3"], 2)
        ]
        
        execution_plan = [["node1"], ["node2", "node3"], ["node4"]]
        
        groups = optimizer._rebuild_parallel_groups(nodes, execution_plan)
        
        # Verify groups structure
        assert isinstance(groups, list)
        
        # Should have parallel group for level 1
        parallel_levels = [group for group in groups if len(group) > 1]
        assert len(parallel_levels) > 0
    
    def test_calculate_critical_path(self, optimizer):
        """Test critical path calculation."""
        nodes = [
            CompiledNode("node1", NodeType.INPUT, None, [], 0),
            CompiledNode("node2", NodeType.LLM, None, ["node1"], 1),
            CompiledNode("node3", NodeType.LLM, None, ["node2"], 2),
            CompiledNode("node4", NodeType.OUTPUT, None, ["node3"], 3)
        ]
        
        dependency_graph = {
            "node1": set(),
            "node2": {"node1"},
            "node3": {"node2"},
            "node4": {"node3"}
        }
        
        critical_path = optimizer._calculate_critical_path(nodes, dependency_graph)
        
        # Verify critical path
        assert isinstance(critical_path, list)
        assert len(critical_path) == 4
        assert critical_path[0] == "node1"
        assert critical_path[-1] == "node4"
    
    def test_optimization_history_tracking(self, optimizer, sample_nodes, execution_plan, parallel_groups):
        """Test that optimization history is tracked."""
        # Run optimization
        asyncio.run(optimizer.optimize_graph(sample_nodes, execution_plan, parallel_groups))
        
        # Verify history was recorded
        assert len(optimizer._optimization_history) == 1
        
        history_entry = optimizer._optimization_history[0]
        assert "timestamp" in history_entry
        assert "results" in history_entry
        assert "original_node_count" in history_entry
        assert "final_node_count" in history_entry
        
        # Verify results in history
        assert len(history_entry["results"]) == 7  # 7 optimization strategies
    
    def test_resource_models_initialization(self, optimizer):
        """Test resource models initialization."""
        resource_models = optimizer._resource_models
        
        # Verify all node types have models
        for node_type in NodeType:
            assert node_type in resource_models
        
        # Verify model structure
        for node_type, model in resource_models.items():
            assert "base_memory_mb" in model
            assert "base_cpu_percent" in model
            assert "base_duration_seconds" in model
    
    def test_cost_models_initialization(self, optimizer):
        """Test cost models initialization."""
        cost_models = optimizer._cost_models
        
        # Verify all node types have models
        for node_type in NodeType:
            assert node_type in cost_models
        
        # Verify model structure
        for node_type, model in cost_models.items():
            assert "cost_per_request" in model
            # LLM nodes should have token cost
            if node_type == NodeType.LLM:
                assert "cost_per_token" in model
                assert "tokens_per_cost_unit" in model


if __name__ == "__main__":
    pytest.main([__file__])