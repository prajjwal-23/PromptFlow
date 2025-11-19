"""
DAG Compiler Service

This module provides comprehensive DAG compilation with topological sorting,
cycle detection, and optimization for graph execution following enterprise-grade patterns.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from collections import defaultdict, deque

from ...domain.execution.models import ExecutionConfig, NodeConfiguration, NodeType, CompiledNode
from ..validation.graph_validator import GraphValidator, ValidationResult, ValidationSeverity


class CompilationStatus(str, Enum):
    """Compilation status levels."""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    OPTIMIZED = "optimized"


@dataclass(frozen=True)
class CompilationResult:
    """Result of DAG compilation."""
    is_valid: bool
    status: CompilationStatus
    nodes: List[CompiledNode] = field(default_factory=list)
    execution_plan: List[List[str]] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    optimization_applied: List[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "status": self.status.value,
            "nodes": [node.to_dict() for node in self.nodes],
            "execution_plan": self.execution_plan,
            "parallel_groups": self.parallel_groups,
            "metadata": self.metadata,
            "errors": self.errors,
            "warnings": self.warnings,
            "optimization_applied": self.optimization_applied,
        }


class DAGCompiler:
    """Enterprise-grade DAG compiler with topological sorting and optimization."""
    
    def __init__(self):
        """Initialize the DAG compiler."""
        self._validator = GraphValidator()
        self._optimization_rules = self._create_optimization_rules()
    
    def _create_optimization_rules(self) -> List[str]:
        """Create optimization rules for DAG compilation."""
        return [
            "dead_code_elimination",
            "parallel_execution_optimization",
            "node_merging",
            "edge_optimization",
            "subgraph_extraction",
        ]
    
    async def compile_graph(
        self,
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> CompilationResult:
        """
        Compile graph JSON into executable DAG with topological sorting.
        
        Args:
            graph_json: Graph JSON to compile
            config: Execution configuration for context
            
        Returns:
            CompilationResult with compiled DAG and execution plan
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Validate graph structure
            validation_result = await self._validator.validate_graph(graph_json, config)
            if not validation_result.is_valid:
                return CompilationResult(
                    is_valid=False,
                    status=CompilationStatus.FAILED,
                    errors=[f"Validation failed: {error.message}" for error in validation_result.errors],
                    metadata={"compilation_time": (datetime.now() - start_time).total_seconds()}
                )
            
            # Step 2: Extract nodes and edges
            nodes = graph_json.get("nodes", [])
            edges = graph_json.get("edges", [])
            
            # Step 3: Build adjacency list and dependency graph
            adjacency = self._build_adjacency_list(nodes, edges)
            dependency_graph = self._build_dependency_graph(nodes, edges)
            
            # Step 4: Detect cycles
            cycle_result = await self._detect_cycles(dependency_graph)
            if cycle_result.has_cycles:
                return CompilationResult(
                    is_valid=False,
                    status=CompilationStatus.FAILED,
                    errors=[f"Cycle detected: {cycle_result.cycle_path}"],
                    metadata={"compilation_time": (datetime.now() - start_time).total_seconds()}
                )
            
            # Step 5: Topological sorting
            topological_order = await self._topological_sort(dependency_graph)
            if not topological_order:
                return CompilationResult(
                    is_valid=False,
                    status=CompilationStatus.FAILED,
                    errors=["Failed to perform topological sorting"],
                    metadata={"compilation_time": (datetime.now() - start_time).total_seconds()}
                )
            
            # Step 6: Create compiled nodes
            compiled_nodes = self._create_compiled_nodes(nodes, dependency_graph, topological_order)
            
            # Step 7: Generate execution plan
            execution_plan = self._generate_execution_plan(compiled_nodes)
            
            # Step 8: Identify parallel groups
            parallel_groups = self._identify_parallel_groups(compiled_nodes)
            
            # Step 9: Apply optimizations
            optimization_result = await self._apply_optimizations(
                compiled_nodes, execution_plan, parallel_groups, config
            )
            
            # Step 10: Create final result
            compilation_time = (datetime.now() - start_time).total_seconds()
            
            return CompilationResult(
                is_valid=True,
                status=CompilationStatus.SUCCESS if not optimization_result.warnings else CompilationStatus.WARNING,
                nodes=optimization_result.nodes,
                execution_plan=optimization_result.execution_plan,
                parallel_groups=optimization_result.parallel_groups,
                metadata={
                    "compilation_time": compilation_time,
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "validation_time": validation_result.metrics.get("validation_time", 0),
                    "topological_sort_time": compilation_time - validation_result.metrics.get("validation_time", 0),
                },
                warnings=validation_result.warnings + optimization_result.warnings,
                optimization_applied=optimization_result.optimization_applied,
            )
            
        except Exception as e:
            return CompilationResult(
                is_valid=False,
                status=CompilationStatus.FAILED,
                errors=[f"Compilation failed: {str(e)}"],
                metadata={"compilation_time": (datetime.now() - start_time).total_seconds()}
            )
    
    def _build_adjacency_list(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Build adjacency list from nodes and edges."""
        adjacency = {node["id"]: [] for node in nodes}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in adjacency and target in adjacency:
                adjacency[source].append(target)
        return adjacency
    
    def _build_dependency_graph(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Set[str]]:
        """Build dependency graph (reverse adjacency)."""
        dependencies = {node["id"]: set() for node in nodes}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in dependencies and target in dependencies:
                dependencies[target].add(source)
        return dependencies
    
    async def _detect_cycles(self, dependency_graph: Dict[str, Set[str]]) -> "CycleDetectionResult":
        """Detect cycles using DFS with cycle path reconstruction."""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str, parent: Optional[str] = None) -> Optional[List[str]]:
            if node in rec_stack:
                # Cycle detected - find the cycle path
                cycle_start_index = path.index(node)
                return path[cycle_start_index:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependency_graph.get(node, []):
                if neighbor != parent:  # Avoid going back to parent
                    cycle_path = dfs(neighbor, node)
                    if cycle_path:
                        return cycle_path
            
            rec_stack.remove(node)
            path.pop()
            return None
        
        for node in dependency_graph:
            if node not in visited:
                cycle_path = dfs(node)
                if cycle_path:
                    return CycleDetectionResult(
                        has_cycles=True,
                        cycle_path=" -> ".join(cycle_path)
                    )
        
        return CycleDetectionResult(has_cycles=False)
    
    async def _topological_sort(self, dependency_graph: Dict[str, Set[str]]) -> List[str]:
        """Perform topological sort using Kahn's algorithm."""
        # Calculate in-degree for each node
        in_degree = {node: 0 for node in dependency_graph}
        for node in dependency_graph:
            for neighbor in dependency_graph[node]:
                in_degree[neighbor] += 1
        
        # Initialize queue with nodes having zero in-degree
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        topological_order = []
        
        while queue:
            current = queue.popleft()
            topological_order.append(current)
            
            # Decrease in-degree for neighbors
            for neighbor in dependency_graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if topological sort is complete
        if len(topological_order) != len(dependency_graph):
            return []  # Cycle detected
        
        return topological_order
    
    def _create_compiled_nodes(
        self, 
        nodes: List[Dict[str, Any]], 
        dependency_graph: Dict[str, Set[str]],
        topological_order: List[str]
    ) -> List[CompiledNode]:
        """Create compiled nodes with execution metadata."""
        compiled_nodes = []
        node_map = {node["id"]: node for node in nodes}
        
        # Create reverse dependency graph for dependents
        dependents = {node["id"]: set() for node in nodes}
        for node_id, dependencies in dependency_graph.items():
            for dep in dependencies:
                dependents[dep].add(node_id)
        
        for i, node_id in enumerate(topological_order):
            if node_id not in node_map:
                continue
            
            node = node_map[node_id]
            compiled_node = CompiledNode(
                id=node_id,
                type=NodeType(node["type"]),
                config=node.get("data", {}),
                dependencies=list(dependency_graph.get(node_id, [])),
                dependents=list(dependents.get(node_id, [])),
                execution_order=i,
                parallel_group=0,  # Will be updated later
                metadata={
                    "position": node.get("position", {}),
                    "created_at": datetime.now().isoformat(),
                }
            )
            compiled_nodes.append(compiled_node)
        
        return compiled_nodes
    
    def _generate_execution_plan(self, compiled_nodes: List[CompiledNode]) -> List[List[str]]:
        """Generate execution plan with dependency levels."""
        if not compiled_nodes:
            return []
        
        # Group nodes by execution order
        execution_levels = defaultdict(list)
        max_order = max(node.execution_order for node in compiled_nodes)
        
        for node in compiled_nodes:
            execution_levels[node.execution_order].append(node.id)
        
        # Create execution plan
        execution_plan = []
        for i in range(max_order + 1):
            if i in execution_levels:
                execution_plan.append(execution_levels[i])
        
        return execution_plan
    
    def _identify_parallel_groups(self, compiled_nodes: List[CompiledNode]) -> List[List[str]]:
        """Identify groups of nodes that can be executed in parallel."""
        if not compiled_nodes:
            return []
        
        # Group nodes by their dependencies
        parallel_groups = []
        processed_nodes = set()
        
        for node in compiled_nodes:
            if node.id in processed_nodes:
                continue
            
            # Find nodes with same dependencies
            current_group = [node.id]
            processed_nodes.add(node.id)
            
            for other_node in compiled_nodes:
                if (other_node.id not in processed_nodes and 
                    set(other_node.dependencies) == set(node.dependencies) and
                    other_node.execution_order == node.execution_order):
                    current_group.append(other_node.id)
                    processed_nodes.add(other_node.id)
            
            parallel_groups.append(current_group)
        
        return parallel_groups
    
    async def _apply_optimizations(
        self,
        compiled_nodes: List[CompiledNode],
        execution_plan: List[List[str]],
        parallel_groups: List[List[str]],
        config: Optional[ExecutionConfig] = None
    ) -> "OptimizationResult":
        """Apply various optimizations to the compiled DAG."""
        optimizations_applied = []
        warnings = []
        
        # Optimization 1: Dead code elimination
        dead_code_result = await self._eliminate_dead_code(compiled_nodes, execution_plan)
        if dead_code_result.eliminated_nodes:
            optimizations_applied.append("dead_code_elimination")
            compiled_nodes = dead_code_result.nodes
            execution_plan = dead_code_result.execution_plan
            warnings.extend(dead_code_result.warnings)
        
        # Optimization 2: Parallel execution optimization
        parallel_result = await self._optimize_parallel_execution(compiled_nodes, execution_plan)
        if parallel_result.optimized:
            optimizations_applied.append("parallel_execution_optimization")
            parallel_groups = parallel_result.parallel_groups
        
        # Optimization 3: Node merging (if applicable)
        merge_result = await self._merge_compatible_nodes(compiled_nodes)
        if merge_result.merged_nodes:
            optimizations_applied.append("node_merging")
            compiled_nodes = merge_result.nodes
            warnings.extend(merge_result.warnings)
        
        return OptimizationResult(
            nodes=compiled_nodes,
            execution_plan=execution_plan,
            parallel_groups=parallel_groups,
            optimizations_applied=optimizations_applied,
            warnings=warnings
        )
    
    async def _eliminate_dead_code(
        self, 
        compiled_nodes: List[CompiledNode], 
        execution_plan: List[List[str]]
    ) -> "DeadCodeEliminationResult":
        """Eliminate nodes that are not connected to output."""
        if not compiled_nodes:
            return DeadCodeEliminationResult(
                nodes=compiled_nodes,
                execution_plan=execution_plan,
                eliminated_nodes=[],
                warnings=[]
            )
        
        # Find output nodes
        output_nodes = [node for node in compiled_nodes if node.type == NodeType.OUTPUT]
        if not output_nodes:
            return DeadCodeEliminationResult(
                nodes=compiled_nodes,
                execution_plan=execution_plan,
                eliminated_nodes=[],
                warnings=["No output nodes found for dead code elimination"]
            )
        
        # Find all nodes that lead to output
        reachable_nodes = set()
        queue = deque(output_nodes)
        
        while queue:
            current = queue.popleft()
            if current.id in reachable_nodes:
                continue
            
            reachable_nodes.add(current.id)
            queue.extend(
                compiled_node for compiled_node in compiled_nodes 
                if compiled_node.id in current.dependencies
            )
        
        # Filter out unreachable nodes
        eliminated_nodes = []
        filtered_nodes = []
        for node in compiled_nodes:
            if node.id in reachable_nodes:
                filtered_nodes.append(node)
            else:
                eliminated_nodes.append(node.id)
        
        # Update execution plan
        filtered_execution_plan = []
        for level in execution_plan:
            filtered_level = [node_id for node_id in level if node_id in reachable_nodes]
            if filtered_level:
                filtered_execution_plan.append(filtered_level)
        
        warnings = [f"Eliminated {len(eliminated_nodes)} dead code nodes"] if eliminated_nodes else []
        
        return DeadCodeEliminationResult(
            nodes=filtered_nodes,
            execution_plan=filtered_execution_plan,
            eliminated_nodes=eliminated_nodes,
            warnings=warnings
        )
    
    async def _optimize_parallel_execution(
        self, 
        compiled_nodes: List[CompiledNode], 
        execution_plan: List[List[str]]
    ) -> "ParallelOptimizationResult":
        """Optimize parallel execution by identifying independent nodes."""
        if len(compiled_nodes) < 2:
            return ParallelOptimizationResult(
                optimized=False,
                parallel_groups=[]
            )
        
        # Create dependency map
        dependency_map = {node.id: set(node.dependencies) for node in compiled_nodes}
        
        # Identify independent nodes at each level
        optimized_groups = []
        for level in execution_plan:
            if len(level) <= 1:
                optimized_groups.append(level)
                continue
            
            # Group nodes by dependencies
            dependency_groups = defaultdict(list)
            for node_id in level:
                deps = frozenset(dependency_map.get(node_id, []))
                dependency_groups[deps].append(node_id)
            
            # Flatten groups
            optimized_level = []
            for group in dependency_groups.values():
                optimized_level.extend(group)
            
            optimized_groups.append(optimized_level)
        
        return ParallelOptimizationResult(
            optimized=True,
            parallel_groups=optimized_groups
        )
    
    async def _merge_compatible_nodes(
        self, 
        compiled_nodes: List[CompiledNode]
    ) -> "NodeMergeResult":
        """Merge compatible nodes to reduce execution overhead."""
        # This is a placeholder for node merging optimization
        # In a real implementation, this would merge nodes with compatible types
        # and similar configurations
        
        merged_nodes = []
        merged_count = 0
        warnings = []
        
        # For now, just return the original nodes
        # Node merging would require more sophisticated logic
        return NodeMergeResult(
            nodes=compiled_nodes,
            merged_nodes=merged_count,
            warnings=warnings
        )


@dataclass(frozen=True)
class CycleDetectionResult:
    """Result of cycle detection."""
    has_cycles: bool
    cycle_path: Optional[str] = None


@dataclass(frozen=True)
class OptimizationResult:
    """Result of optimization process."""
    nodes: List[CompiledNode]
    execution_plan: List[List[str]]
    parallel_groups: List[List[str]]
    optimizations_applied: List[str]
    warnings: List[str]


@dataclass(frozen=True)
class DeadCodeEliminationResult:
    """Result of dead code elimination."""
    nodes: List[CompiledNode]
    execution_plan: List[List[str]]
    eliminated_nodes: List[str]
    warnings: List[str]


@dataclass(frozen=True)
class ParallelOptimizationResult:
    """Result of parallel execution optimization."""
    optimized: bool
    parallel_groups: List[List[str]]


@dataclass(frozen=True)
class NodeMergeResult:
    """Result of node merging optimization."""
    nodes: List[CompiledNode]
    merged_nodes: int
    warnings: List[str]


class DAGCompilationService:
    """Enterprise-grade DAG compilation service with caching and optimization."""
    
    def __init__(self):
        """Initialize the compilation service."""
        self._compiler = DAGCompiler()
        self._cache = {}
        self._metrics = {
            "compilations_performed": 0,
            "total_compilation_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_compilation_time": 0.0,
            "optimizations_applied": 0,
        }
    
    async def compile_graph(
        self,
        graph_json: Dict[str, Any],
        config: Optional[ExecutionConfig] = None
    ) -> CompilationResult:
        """
        Compile graph with comprehensive optimization.
        
        Args:
            graph_json: Graph JSON to compile
            config: Execution configuration for context
            
        Returns:
            CompilationResult with compiled DAG and execution plan
        """
        start_time = datetime.now()
        
        # Update metrics
        self._metrics["compilations_performed"] += 1
        
        # Check cache first
        cache_key = self._get_cache_key(graph_json, config)
        if cache_key in self._cache:
            self._metrics["cache_hits"] += 1
            return self._cache[cache_key]
        
        self._metrics["cache_misses"] += 1
        
        # Perform compilation
        result = await self._compiler.compile_graph(graph_json, config)
        
        # Update metrics
        compilation_time = (datetime.now() - start_time).total_seconds()
        self._metrics["total_compilation_time"] += compilation_time
        self._metrics["average_compilation_time"] = (
            self._metrics["total_compilation_time"] / self._metrics["compilations_performed"]
        )
        self._metrics["optimizations_applied"] += len(result.optimization_applied)
        
        # Cache successful compilations
        if result.is_valid:
            self._cache[cache_key] = result
        
        return result
    
    def _get_cache_key(self, graph_json: Dict[str, Any], config: Optional[ExecutionConfig] = None) -> str:
        """Generate cache key for graph compilation."""
        graph_str = json.dumps(graph_json, sort_keys=True)
        config_str = json.dumps(config.to_dict() if config else {}, sort_keys=True)
        return f"compile_{hash(graph_str + config_str)}"
    
    def get_compilation_metrics(self) -> Dict[str, Any]:
        """Get compilation performance metrics."""
        return self._metrics.copy()
    
    def clear_cache(self) -> None:
        """Clear the compilation cache."""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._metrics.get("compilations_performed", 0)
        cache_hits = self._metrics.get("cache_hits", 0)
        cache_misses = total_requests - cache_hits
        
        return {
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate": (cache_hits / total_requests * 100) if total_requests > 0 else 0,
            "average_compilation_time": self._metrics.get("average_compilation_time", 0.0),
            "cache_size": len(self._cache),
            "optimizations_applied": self._metrics.get("optimizations_applied", 0),
        }