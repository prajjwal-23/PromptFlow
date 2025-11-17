"""
Execution Context Manager

This module provides the execution context management system with proper
lifecycle handling, resource allocation, and state persistence following enterprise-grade patterns.
"""

from __future__ import annotations
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import threading
from contextlib import asynccontextmanager
import weakref

from ..domain.models import ExecutionConfig, NodeConfiguration
from ..nodes.base_node import NodeOutput, NodeStatus
from ...domain.events import DomainEvent


class ContextStatus(str, Enum):
    """Context status enumeration."""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CLEANED_UP = "cleaned_up"


@dataclass
class ContextMetrics:
    """Context execution metrics."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_execution_time: float = 0.0
    node_execution_times: Dict[str, float] = field(default_factory=dict)
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    nodes_completed: int = 0
    nodes_failed: int = 0
    nodes_skipped: int = 0
    events_emitted: int = 0
    context_switches: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_execution_time": self.total_execution_time,
            "node_execution_times": self.node_execution_times,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "nodes_completed": self.nodes_completed,
            "nodes_failed": self.nodes_failed,
            "nodes_skipped": self.nodes_skipped,
            "events_emitted": self.events_emitted,
            "context_switches": self.context_switches,
        }


@dataclass
class ExecutionContext:
    """Individual execution context for a single run."""
    execution_id: str
    workspace_id: str
    user_id: str
    agent_id: str
    config: ExecutionConfig
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, NodeOutput] = field(default_factory=dict)
    global_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: ContextStatus = ContextStatus.CREATED
    metrics: ContextMetrics = field(default_factory=ContextMetrics)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    parent_context_id: Optional[str] = None
    child_context_ids: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Post-initialization setup."""
        if not self.execution_id:
            self.execution_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "node_outputs": {k: v.to_dict() for k, v in self.node_outputs.items()},
            "global_state": self.global_state,
            "metadata": self.metadata,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parent_context_id": self.parent_context_id,
            "child_context_ids": list(self.child_context_ids),
        }
    
    def update_status(self, status: ContextStatus) -> None:
        """Update context status."""
        self.status = status
        self.updated_at = datetime.now()
        
        if status == ContextStatus.COMPLETED:
            self.end_time = datetime.now()
            self.total_execution_time = (self.end_time - self.metrics.start_time).total_seconds()
    
    def set_node_output(self, node_id: str, output: NodeOutput) -> None:
        """Set node output."""
        self.node_outputs[node_id] = output
        self.updated_at = datetime.now()
        
        # Update metrics
        if output.error:
            self.metrics.nodes_failed += 1
        else:
            self.metrics.nodes_completed += 1
        
        self.metrics.node_execution_times[node_id] = output.execution_time
    
    def get_node_output(self, node_id: str) -> Optional[NodeOutput]:
        """Get node output."""
        return self.node_outputs.get(node_id)
    
    def has_node_output(self, node_id: str) -> bool:
        """Check if node has output."""
        return node_id in self.node_outputs
    
    def get_dependency_output(self, dependency_id: str) -> Optional[NodeOutput]:
        """Get dependency output for node execution."""
        return self.get_node_output(dependency_id)
    
    def set_global_state(self, key: str, value: Any) -> None:
        """Set global state value."""
        self.global_state[key] = value
        self.updated_at = datetime.now()
    
    def get_global_state(self, key: str, default: Any = None) -> Any:
        """Get global state value."""
        return self.global_state.get(key, default)
    
    def add_child_context(self, child_context_id: str) -> None:
        """Add child context."""
        self.child_context_ids.add(child_context_id)
        self.updated_at = datetime.now()
    
    def remove_child_context(self, child_context_id: str) -> None:
        """Remove child context."""
        self.child_context_ids.discard(child_context_id)
        self.updated_at = datetime.now()


class ContextManager:
    """Enterprise-grade execution context manager with lifecycle handling."""
    
    def __init__(self, max_concurrent_contexts: int = 100):
        """
        Initialize the context manager.
        
        Args:
            max_concurrent_contexts: Maximum number of concurrent contexts
        """
        self._contexts: Dict[str, ExecutionContext] = {}
        self._active_contexts: Set[str] = set()
        self._context_lock = asyncio.Lock()
        self._max_concurrent_contexts = max_concurrent_contexts
        self._cleanup_interval = timedelta(minutes=30)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_handlers: List[Callable] = []
        self._resource_monitor = None
        self._persistence_enabled = False
        self._metrics = {
            "contexts_created": 0,
            "contexts_completed": 0,
            "contexts_failed": 0,
            "contexts_cleaned": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0,
        }
    
    async def initialize(self) -> None:
        """Initialize the context manager."""
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Initialize resource monitor
        self._resource_monitor = ResourceMonitor()
        await self._resource_monitor.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the context manager."""
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup all active contexts
        await self.cleanup_all_contexts()
        
        # Shutdown resource monitor
        if self._resource_monitor:
            await self._resource_monitor.shutdown()
    
    @asynccontextmanager
    async def create_context(
        self,
        execution_id: Optional[str] = None,
        workspace_id: str = "",
        user_id: str = "",
        agent_id: str = "",
        config: Optional[ExecutionConfig] = None,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_context_id: Optional[str] = None
    ) -> ExecutionContext:
        """
        Create and manage an execution context.
        
        Args:
            execution_id: Unique execution identifier
            workspace_id: Workspace identifier
            user_id: User identifier
            agent_id: Agent identifier
            config: Execution configuration
            inputs: Input data
            metadata: Additional metadata
            parent_context_id: Parent context ID for nested executions
            
        Yields:
            ExecutionContext instance
        """
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        
        # Check concurrent context limit
        async with self._context_lock:
            if len(self._active_contexts) >= self._max_concurrent_contexts:
                raise RuntimeError(f"Maximum concurrent contexts ({self._max_concurrent_contexts}) reached")
            
            # Create context
            context = ExecutionContext(
                execution_id=execution_id,
                workspace_id=workspace_id,
                user_id=user_id,
                agent_id=agent_id,
                config=config or ExecutionConfig(),
                inputs=inputs or {},
                metadata=metadata or {},
                parent_context_id=parent_context_id
            )
            
            # Store context
            self._contexts[execution_id] = context
            self._active_contexts.add(execution_id)
            
            # Update metrics
            self._metrics["contexts_created"] += 1
            
            # Add to parent context if specified
            if parent_context_id and parent_context_id in self._contexts:
                self._contexts[parent_context_id].add_child_context(execution_id)
            
            # Emit event
            await self._emit_event("context_created", {
                "execution_id": execution_id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "agent_id": agent_id,
            })
        
        try:
            # Initialize context
            context.update_status(ContextStatus.INITIALIZING)
            await self._initialize_context(context)
            context.update_status(ContextStatus.READY)
            
            yield context
            
        except Exception as e:
            context.update_status(ContextStatus.FAILED)
            self._metrics["contexts_failed"] += 1
            await self._emit_event("context_failed", {
                "execution_id": execution_id,
                "error": str(e),
            })
            raise
        finally:
            # Cleanup context
            await self._cleanup_context(execution_id)
    
    async def _initialize_context(self, context: ExecutionContext) -> None:
        """Initialize context with required setup."""
        # Set up global state
        context.set_global_state("execution_id", context.execution_id)
        context.set_global_state("workspace_id", context.workspace_id)
        context.set_global_state("user_id", context.user_id)
        context.set_global_state("agent_id", context.agent_id)
        context.set_global_state("start_time", context.metrics.start_time.isoformat())
        
        # Initialize resource monitoring
        if self._resource_monitor:
            await self._resource_monitor.start_monitoring(context.execution_id)
        
        # Persist context if enabled
        if self._persistence_enabled:
            await self._persist_context(context)
    
    async def get_context(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get context by execution ID."""
        async with self._context_lock:
            return self._contexts.get(execution_id)
    
    async def update_context_status(self, execution_id: str, status: ContextStatus) -> None:
        """Update context status."""
        async with self._context_lock:
            if execution_id in self._contexts:
                self._contexts[execution_id].update_status(status)
                
                # Update metrics
                if status == ContextStatus.COMPLETED:
                    self._metrics["contexts_completed"] += 1
                    total_time = self._contexts[execution_id].metrics.total_execution_time
                    self._metrics["total_execution_time"] += total_time
                    self._metrics["average_execution_time"] = (
                        self._metrics["total_execution_time"] / self._metrics["contexts_completed"]
                    )
                elif status == ContextStatus.FAILED:
                    self._metrics["contexts_failed"] += 1
                
                # Emit event
                await self._emit_event("context_status_updated", {
                    "execution_id": execution_id,
                    "status": status.value,
                })
    
    async def cleanup_context(self, execution_id: str) -> None:
        """Clean up a specific context."""
        async with self._context_lock:
            if execution_id in self._contexts:
                context = self._contexts[execution_id]
                
                # Update status
                if context.status not in [ContextStatus.COMPLETED, ContextStatus.FAILED, ContextStatus.CANCELLED]:
                    context.update_status(ContextStatus.CLEANED_UP)
                
                # Remove from active contexts
                self._active_contexts.discard(execution_id)
                
                # Stop resource monitoring
                if self._resource_monitor:
                    await self._resource_monitor.stop_monitoring(execution_id)
                
                # Remove from parent context
                if context.parent_context_id and context.parent_context_id in self._contexts:
                    self._contexts[context.parent_context_id].remove_child_context(execution_id)
                
                # Update metrics
                self._metrics["contexts_cleaned"] += 1
                
                # Emit event
                await self._emit_event("context_cleaned", {
                    "execution_id": execution_id,
                })
    
    async def cleanup_all_contexts(self) -> None:
        """Clean up all contexts."""
        context_ids = list(self._contexts.keys())
        for execution_id in context_ids:
            await self.cleanup_context(execution_id)
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval.total_seconds())
                await self._cleanup_expired_contexts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue cleanup
                print(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_contexts(self) -> None:
        """Clean up expired contexts."""
        current_time = datetime.now()
        expired_threshold = current_time - self._cleanup_interval
        
        async with self._context_lock:
            expired_contexts = [
                execution_id for execution_id, context in self._contexts.items()
                if (context.updated_at < expired_threshold and 
                    context.status in [ContextStatus.COMPLETED, ContextStatus.FAILED, ContextStatus.CANCELLED])
            ]
            
            for execution_id in expired_contexts:
                await self.cleanup_context(execution_id)
    
    def add_event_handler(self, handler: Callable) -> None:
        """Add event handler."""
        self._event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable) -> None:
        """Remove event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
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
    
    async def _persist_context(self, context: ExecutionContext) -> None:
        """Persist context to storage."""
        # This would integrate with your persistence layer
        # For now, we'll just log it
        pass
    
    def get_active_contexts(self) -> List[str]:
        """Get list of active context IDs."""
        return list(self._active_contexts)
    
    def get_context_count(self) -> int:
        """Get total number of contexts."""
        return len(self._contexts)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get context manager metrics."""
        return self._metrics.copy()
    
    async def get_context_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get context summary."""
        context = await self.get_context(execution_id)
        if not context:
            return None
        
        return {
            "execution_id": context.execution_id,
            "status": context.status.value,
            "workspace_id": context.workspace_id,
            "user_id": context.user_id,
            "agent_id": context.agent_id,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "metrics": context.metrics.to_dict(),
            "node_count": len(context.node_outputs),
            "has_parent": context.parent_context_id is not None,
            "child_count": len(context.child_context_ids),
        }


class ResourceMonitor:
    """Resource monitoring for execution contexts."""
    
    def __init__(self):
        """Initialize the resource monitor."""
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._resource_data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the resource monitor."""
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the resource monitor."""
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        self._monitoring_tasks.clear()
        self._resource_data.clear()
    
    async def start_monitoring(self, execution_id: str) -> None:
        """Start monitoring a context."""
        async with self._lock:
            if execution_id not in self._monitoring_tasks:
                self._monitoring_tasks[execution_id] = asyncio.create_task(
                    self._monitor_resources(execution_id)
                )
                self._resource_data[execution_id] = {
                    "start_time": datetime.now(),
                    "memory_usage": [],
                    "cpu_usage": [],
                    "peak_memory": 0.0,
                    "peak_cpu": 0.0,
                }
    
    async def stop_monitoring(self, execution_id: str) -> None:
        """Stop monitoring a context."""
        async with self._lock:
            if execution_id in self._monitoring_tasks:
                task = self._monitoring_tasks.pop(execution_id)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def _monitor_resources(self, execution_id: str) -> None:
        """Monitor resources for a context."""
        try:
            while execution_id in self._monitoring_tasks:
                # Mock resource monitoring
                import psutil
                import os
                
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                
                async with self._lock:
                    if execution_id in self._resource_data:
                        data = self._resource_data[execution_id]
                        data["memory_usage"].append(memory_info.rss / 1024 / 1024)  # MB
                        data["cpu_usage"].append(cpu_percent)
                        data["peak_memory"] = max(data["peak_memory"], data["memory_usage"][-1])
                        data["peak_cpu"] = max(data["peak_cpu"], data["cpu_usage"][-1])
                
                await asyncio.sleep(1)  # Monitor every second
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Resource monitoring error for {execution_id}: {e}")
    
    def get_resource_data(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get resource data for a context."""
        return self._resource_data.get(execution_id)


# Global context manager instance
_default_context_manager = None


def get_default_context_manager() -> ContextManager:
    """Get the default context manager instance."""
    global _default_context_manager
    if _default_context_manager is None:
        _default_context_manager = ContextManager()
    return _default_context_manager


@asynccontextmanager
async def create_execution_context(
    execution_id: Optional[str] = None,
    workspace_id: str = "",
    user_id: str = "",
    agent_id: str = "",
    config: Optional[ExecutionConfig] = None,
    inputs: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    manager: Optional[ContextManager] = None
) -> ExecutionContext:
    """
    Convenience function to create an execution context.
    
    Args:
        execution_id: Unique execution identifier
        workspace_id: Workspace identifier
        user_id: User identifier
        agent_id: Agent identifier
        config: Execution configuration
        inputs: Input data
        metadata: Additional metadata
        manager: Custom context manager instance
        
    Yields:
        ExecutionContext instance
    """
    if manager is None:
        manager = get_default_context_manager()
    
    async with manager.create_context(
        execution_id=execution_id,
        workspace_id=workspace_id,
        user_id=user_id,
        agent_id=agent_id,
        config=config,
        inputs=inputs,
        metadata=metadata
    ) as context:
        yield context