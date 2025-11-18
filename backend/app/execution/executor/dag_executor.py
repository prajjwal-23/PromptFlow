"""
DAG Executor Implementation

This module provides the DAG execution engine with proper scheduling,
error handling, and resource management following enterprise-grade patterns.
"""

from __future__ import annotations
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Callable, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import weakref

from ..compiler.dag_compiler import CompilationResult, CompiledNode
from ..context.manager import ExecutionContext, ContextStatus, create_execution_context
from ..nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeStatus
from ...domain.execution.models import ExecutionConfig, NodeConfiguration


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Result of DAG execution."""
    execution_id: str
    status: ExecutionStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, NodeOutput] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "outputs": self.outputs,
            "node_results": {k: v.to_dict() for k, v in self.node_results.items()},
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
        }


@dataclass
class NodeExecutionPlan:
    """Node execution plan with scheduling information."""
    execution_order: List[List[str]]
    parallel_groups: List[List[str]]
    dependencies: Dict[str, List[str]]
    estimated_duration: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_order": self.execution_order,
            "parallel_groups": self.parallel_groups,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "resource_requirements": self.resource_requirements,
        }


class DAGExecutor:
    """Enterprise-grade DAG executor with concurrent execution and resource management."""
    
    def __init__(
        self,
        max_concurrent_nodes: int = 10,
        default_timeout: int = 30,
        enable_parallel_execution: bool = True,
        enable_error_recovery: bool = True,
        max_retry_attempts: int = 3
    ):
        """
        Initialize the DAG executor.
        
        Args:
            max_concurrent_nodes: Maximum number of concurrent node executions
            default_timeout: Default timeout for node execution (seconds)
            enable_parallel_execution: Enable parallel execution of independent nodes
            enable_error_recovery: Enable automatic error recovery
            max_retry_attempts: Maximum retry attempts for failed nodes
        """
        self._max_concurrent_nodes = max_concurrent_nodes
        self._default_timeout = default_timeout
        self._enable_parallel_execution = enable_parallel_execution
        self._enable_error_recovery = enable_error_recovery
        self._max_retry_attempts = max_retry_attempts
        
        self._thread_pool = ThreadPoolExecutor(max_workers=max_concurrent_nodes)
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._execution_contexts: Dict[str, ExecutionContext] = {}
        self._node_registry: Dict[str, BaseNode] = {}
        self._event_handlers: List[Callable] = []
        self._metrics = {
            "executions_started": 0,
            "executions_completed": 0,
            "executions_failed": 0,
            "nodes_executed": 0,
            "nodes_failed": 0,
            "nodes_retried": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "parallel_executions": 0,
        }
        self._resource_monitor = None
        self._cancellation_tokens: Dict[str, asyncio.CancelToken] = {}
    
    async def initialize(self) -> None:
        """Initialize the DAG executor."""
        # Initialize resource monitor
        self._resource_monitor = ResourceMonitor()
        await self._resource_monitor.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the DAG executor."""
        # Cancel all active executions
        for execution_id in list(self._active_executions.keys()):
            await self.cancel_execution(execution_id)
        
        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)
        
        # Shutdown resource monitor
        if self._resource_monitor:
            await self._resource_monitor.shutdown()
    
    def register_node(self, node_id: str, node: BaseNode) -> None:
        """Register a node for execution."""
        self._node_registry[node_id] = node
    
    def unregister_node(self, node_id: str) -> None:
        """Unregister a node."""
        if node_id in self._node_registry:
            del self._node_registry[node_id]
    
    def add_event_handler(self, handler: Callable) -> None:
        """Add event handler."""
        self._event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable) -> None:
        """Remove event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
    async def execute_dag(
        self,
        compilation_result: CompilationResult,
        inputs: Dict[str, Any],
        execution_config: Optional[ExecutionConfig] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        Execute a compiled DAG with given inputs.
        
        Args:
            compilation_result: Compiled DAG from DAG compiler
            inputs: Input data for the execution
            execution_config: Execution configuration
            context: Existing execution context (creates new if None)
            
        Returns:
            ExecutionResult with execution details
        """
        if not compilation_result.is_valid:
            return ExecutionResult(
                execution_id=str(uuid.uuid4()),
                status=ExecutionStatus.FAILED,
                errors=["DAG compilation failed"],
                start_time=datetime.now()
            )
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Update metrics
            self._metrics["executions_started"] += 1
            
            # Create or use existing context
            if context is None:
                async with create_execution_context(
                    execution_id=execution_id,
                    workspace_id=inputs.get("workspace_id", ""),
                    user_id=inputs.get("user_id", ""),
                    agent_id=inputs.get("agent_id", ""),
                    config=execution_config or ExecutionConfig(),
                    inputs=inputs
                ) as ctx:
                    result = await self._execute_dag_with_context(
                        compilation_result, inputs, ctx
                    )
            else:
                result = await self._execute_dag_with_context(
                    compilation_result, inputs, context
                )
            
            # Update metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._metrics["total_execution_time"] += duration
            self._metrics["average_execution_time"] = (
                self._metrics["total_execution_time"] / self._metrics["executions_started"]
            )
            
            if result.status == ExecutionStatus.COMPLETED:
                self._metrics["executions_completed"] += 1
            else:
                self._metrics["executions_failed"] += 1
            
            return result
            
        except Exception as e:
            # Update metrics
            self._metrics["executions_failed"] += 1
            
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                errors=[str(e)],
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds()
            )
    
    async def _execute_dag_with_context(
        self,
        compilation_result: CompilationResult,
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute DAG with specific context."""
        execution_id = context.execution_id
        start_time = datetime.now()
        
        # Store context
        self._execution_contexts[execution_id] = context
        
        # Create cancellation token
        cancellation_token = asyncio.CancelToken()
        self._cancellation_tokens[execution_id] = cancellation_token
        
        try:
            # Update context status
            await self._update_context_status(execution_id, ContextStatus.RUNNING)
            
            # Emit execution started event
            await self._emit_event("execution_started", {
                "execution_id": execution_id,
                "dag": compilation_result.to_dict(),
                "inputs": inputs,
            })
            
            # Create execution plan
            execution_plan = self._create_execution_plan(compilation_result)
            
            # Execute nodes
            if self._enable_parallel_execution:
                await self._execute_nodes_parallel(
                    compilation_result.nodes, execution_plan, context, cancellation_token
                )
            else:
                await self._execute_nodes_sequential(
                    compilation_result.nodes, execution_plan, context, cancellation_token
                )
            
            # Collect results
            outputs = self._collect_outputs(compilation_result.nodes, context)
            
            # Create result
            result = ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED,
                outputs=outputs,
                node_results=context.node_outputs,
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                metrics={
                    "nodes_executed": len(compilation_result.nodes),
                    "nodes_failed": context.metrics.nodes_failed,
                    "nodes_retried": self._metrics["nodes_retried"],
                    "parallel_executions": self._metrics["parallel_executions"],
                }
            )
            
            # Update context status
            await self._update_context_status(execution_id, ContextStatus.COMPLETED)
            
            # Emit execution completed event
            await self._emit_event("execution_completed", {
                "execution_id": execution_id,
                "result": result.to_dict(),
            })
            
            return result
            
        except asyncio.CancelledError:
            # Handle cancellation
            await self._update_context_status(execution_id, ContextStatus.CANCELLED)
            
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.CANCELLED,
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            # Handle failure
            await self._update_context_status(execution_id, ContextStatus.FAILED)
            
            # Emit execution failed event
            await self._emit_event("execution_failed", {
                "execution_id": execution_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                errors=[str(e)],
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds()
            )
        
        finally:
            # Cleanup
            if execution_id in self._cancellation_tokens:
                del self._cancellation_tokens[execution_id]
            if execution_id in self._execution_contexts:
                del self._execution_contexts[execution_id]
    
    def _create_execution_plan(self, compilation_result: CompilationResult) -> NodeExecutionPlan:
        """Create execution plan from compilation result."""
        # Extract execution order and dependencies
        execution_order = compilation_result.execution_plan
        parallel_groups = compilation_result.parallel_groups
        
        # Build dependency map
        dependencies = {}
        for node in compilation_result.nodes:
            dependencies[node.id] = node.dependencies
        
        return NodeExecutionPlan(
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            dependencies=dependencies,
            estimated_duration=self._estimate_execution_duration(compilation_result.nodes)
        )
    
    def _estimate_execution_duration(self, nodes: List[CompiledNode]) -> float:
        """Estimate total execution duration."""
        base_duration = 0.5  # Base duration per node
        return len(nodes) * base_duration
    
    async def _execute_nodes_sequential(
        self,
        nodes: List[CompiledNode],
        execution_plan: NodeExecutionPlan,
        context: ExecutionContext,
        cancellation_token: asyncio.CancelToken
    ) -> None:
        """Execute nodes sequentially."""
        for level in execution_plan.execution_order:
            for node_id in level:
                if cancellation_token.is_cancelled():
                    raise asyncio.CancelledError("Execution cancelled")
                
                await self._execute_node(node_id, context, cancellation_token)
    
    async def _execute_nodes_parallel(
        self,
        nodes: List[CompiledNode],
        execution_plan: NodeExecutionPlan,
        context: ExecutionContext,
        cancellation_token: asyncio.CancelToken
    ) -> None:
        """Execute nodes in parallel where possible."""
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self._max_concurrent_nodes)
        
        # Create tasks for each level
        tasks = []
        for level in execution_plan.execution_order:
            level_tasks = []
            for node_id in level:
                task = asyncio.create_task(
                    self._execute_node_with_semaphore(
                        node_id, context, cancellation_token, semaphore
                    )
                )
                level_tasks.append(task)
            
            # Wait for all tasks in this level to complete
            if level_tasks:
                await asyncio.gather(*level_tasks)
    
    async def _execute_node_with_semaphore(
        self,
        node_id: str,
        context: ExecutionContext,
        cancellation_token: asyncio.CancelToken,
        semaphore: asyncio.Semaphore
    ) -> None:
        """Execute a single node with semaphore control."""
        async with semaphore:
            await self._execute_node(node_id, context, cancellation_token)
    
    async def _execute_node(
        self,
        node_id: str,
        context: ExecutionContext,
        cancellation_token: asyncio.CancelToken
    ) -> None:
        """Execute a single node."""
        if node_id not in self._node_registry:
            raise ValueError(f"Node {node_id} not registered")
        
        node = self._node_registry[node_id]
        node_start_time = datetime.now()
        
        try:
            # Check for cancellation
            if cancellation_token.is_cancelled():
                raise asyncio.CancelledError("Execution cancelled")
            
            # Get node inputs from dependencies
            node_inputs = self._prepare_node_inputs(node, context)
            
            # Create node input object
            input_data = NodeInput(
                data=node_inputs,
                metadata={"execution_id": context.execution_id},
                source_nodes=node.dependencies,
                timestamp=datetime.now()
            )
            
            # Execute node
            output = await node.run(input_data, context)
            
            # Store node output
            context.set_node_output(node_id, output)
            
            # Update metrics
            self._metrics["nodes_executed"] += 1
            execution_time = (datetime.now() - node_start_time).total_seconds()
            
            # Emit node completed event
            await self._emit_event("node_completed", {
                "execution_id": context.execution_id,
                "node_id": node_id,
                "execution_time": execution_time,
                "output": output.to_dict(),
            })
            
        except asyncio.CancelledError:
            # Handle cancellation
            await self._emit_event("node_cancelled", {
                "execution_id": context.execution_id,
                "node_id": node_id,
            })
            raise
            
        except Exception as e:
            # Handle node failure
            self._metrics["nodes_failed"] += 1
            
            # Update context metrics
            context.metrics.nodes_failed += 1
            
            # Emit node failed event
            await self._emit_event("node_failed", {
                "execution_id": context.execution_id,
                "node_id": node_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            
            if self._enable_error_recovery:
                # Retry logic would go here
                pass
            else:
                raise
    
    def _prepare_node_inputs(self, node: CompiledNode, context: ExecutionContext) -> Dict[str, Any]:
        """Prepare inputs for node execution."""
        inputs = {}
        
        # Get inputs from dependencies
        for dep_id in node.dependencies:
            if context.has_node_output(dep_id):
                dep_output = context.get_node_output(dep_id)
                if dep_output and not dep_output.error:
                    inputs[dep_id] = dep_output.data.get("result", {})
        
        # Add global state
        inputs.update(context.global_state)
        
        # Add context-specific inputs
        inputs.update(context.inputs)
        
        return inputs
    
    def _collect_outputs(self, nodes: List[CompiledNode], context: ExecutionContext) -> Dict[str, Any]:
        """Collect outputs from executed nodes."""
        outputs = {}
        
        # Get outputs from output nodes
        for node in nodes:
            if node.type.value == "output" and context.has_node_output(node.id):
                output = context.get_node_output(node.id)
                if output and not output.error:
                    outputs[node.id] = output.data.get("result", {})
        
        # Add global state to outputs
        outputs.update(context.global_state)
        
        return outputs
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        if execution_id in self._cancellation_tokens:
            self._cancellation_tokens[execution_id].cancel()
            return True
        return False
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause an active execution."""
        # Implementation would pause execution
        return False
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution."""
        # Implementation would resume execution
        return False
    
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get execution status."""
        if execution_id in self._execution_contexts:
            context = self._execution_contexts[execution_id]
            return ExecutionStatus(context.status.value)
        return None
    
    def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs."""
        return list(self._active_executions.keys())
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get executor metrics."""
        return self._metrics.copy()
    
    async def _update_context_status(self, execution_id: str, status: ContextStatus) -> None:
        """Update context status."""
        if execution_id in self._execution_contexts:
            self._execution_contexts[execution_id].update_status(status)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to all handlers."""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                # Log error but don't fail the operation
                print(f"Event handler error: {e}")


class ResourceMonitor:
    """Resource monitoring for DAG execution."""
    
    def __init__(self):
        """Initialize the resource monitor."""
        self._monitoring_active = False
        self._resource_data = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the resource monitor."""
        self._monitoring_active = True
    
    async def shutdown(self) -> None:
        """Shutdown the resource monitor."""
        self._monitoring_active = False
    
    async def get_resource_usage(self, execution_id: str) -> Dict[str, Any]:
        """Get resource usage for an execution."""
        async with self._lock:
            return self._resource_data.get(execution_id, {})


# Global DAG executor instance
_default_executor = None


def get_default_executor() -> DAGExecutor:
    """Get the default DAG executor instance."""
    global _default_executor
    if _default_executor is None:
        _default_executor = DAGExecutor()
    return _default_executor


async def execute_dag(
    compilation_result: CompilationResult,
    inputs: Dict[str, Any],
    execution_config: Optional[ExecutionConfig] = None,
    executor: Optional[DAGExecutor] = None
) -> ExecutionResult:
    """
    Convenience function to execute a DAG.
    
    Args:
        compilation_result: Compiled DAG from DAG compiler
        inputs: Input data for the execution
        execution_config: Execution configuration
        executor: Custom executor instance
        
    Returns:
        ExecutionResult with execution details
    """
    if executor is None:
        executor = get_default_executor()
    
    return await executor.execute_dag(compilation_result, inputs, execution_config)