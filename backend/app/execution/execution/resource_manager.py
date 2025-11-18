"""
Resource Manager Implementation

This module provides resource management for DAG execution with proper
monitoring, allocation, and cleanup following enterprise-grade patterns.
"""

from __future__ import annotations
import asyncio
import psutil
import threading
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import weakref
from contextlib import asynccontextmanager

from ...domain.execution.models import ExecutionConfig
from ..nodes.base_node import BaseNode


class ResourceType(str, Enum):
    """Resource type enumeration."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


@dataclass
class ResourceUsage:
    """Resource usage information."""
    resource_type: ResourceType
    current_usage: float
    peak_usage: float
    average_usage: float
    timestamp: datetime = field(default_factory=datetime.now)
    process_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_type": self.resource_type.value,
            "current_usage": self.current_usage,
            "peak_usage": self.peak_usage,
            "average_usage": self.average_usage,
            "timestamp": self.timestamp.isoformat(),
            "process_id": self.process_id,
            "metadata": self.metadata,
        }


@dataclass
class ResourceLimits:
    """Resource limits configuration."""
    max_cpu_usage: float = 80.0  # 80% CPU usage
    max_memory_usage: float = 70.0  # 70% memory usage
    max_disk_usage: float = 90.0  # 90% disk usage
    max_network_connections: int = 1000
    max_gpu_usage: float = 90.0  # 90% GPU usage
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "max_cpu_usage": self.max_cpu_usage,
            "max_memory_usage": self.max_memory_usage,
            "max_disk_usage": self.max_disk_usage,
            "max_network_connections": self.max_network_connections,
            "max_gpu_usage": self.max_gpu_usage,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class ResourceAllocation:
    """Resource allocation for a specific execution."""
    execution_id: str
    resource_limits: ResourceLimits
    allocated_resources: Dict[ResourceType, float] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "allocated_resources": {k: v for k, v in self.allocated_resources.items()},
            "resource_limits": self.resource_limits.to_dict(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "metadata": self.metadata,
        }


class ResourceManager:
    """Enterprise-grade resource manager for DAG execution."""
    
    def __init__(
        self,
        max_concurrent_executions: int = 10,
        resource_limits: Optional[ResourceLimits] = None,
        monitoring_interval: float = 1.0,
        enable_auto_scaling: bool = True
    ):
        """
        Initialize the resource manager.
        
        Args:
            max_concurrent_executions: Maximum concurrent executions
            resource_limits: Resource limits configuration
            monitoring_interval: Monitoring interval in seconds
            enable_auto_scaling: Enable automatic resource scaling
        """
        self._max_concurrent_executions = max_concurrent_executions
        self._resource_limits = resource_limits or ResourceLimits()
        self._monitoring_interval = monitoring_interval
        self._enable_auto_scaling = enable_auto_scaling
        
        self._active_allocations: Dict[str, ResourceAllocation] = {}
        self._resource_usage_history: List[ResourceUsage] = []
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._resource_pools: Dict[ResourceType, List[float]] = {
            ResourceType.CPU: [],
            ResourceType.MEMORY: [],
            ResourceType.DISK: [],
            ResourceType.NETWORK: [],
            ResourceType.GPU: [],
        }
        
        self._lock = asyncio.Lock()
        self._event_handlers: List[Callable] = []
        self._metrics = {
            "allocations_created": 0,
            "allocations_completed": 0,
            "allocations_failed": 0,
            "resource_violations": 0,
            "auto_scaling_events": 0,
            "total_monitoring_time": 0.0,
            "peak_cpu_usage": 0.0,
            "peak_memory_usage": 0.0,
            "average_cpu_usage": 0.0,
            "average_memory_usage": 0.0,
        }
        
        self._process = psutil.Process()
        self._system_info = self._get_system_info()
    
    async def initialize(self) -> None:
        """Initialize the resource manager."""
        # Start monitoring tasks
        self._monitoring_tasks["system"] = asyncio.create_task(self._monitor_system_resources())
        
        # Initialize resource pools
        await self._initialize_resource_pools()
        
        # Start auto-scaling if enabled
        if self._enable_auto_scaling:
            self._monitoring_tasks["auto_scaling"] = asyncio.create_task(self._auto_scaling_loop())
    
    async def shutdown(self) -> None:
        """Shutdown the resource manager."""
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        # Clean up all active allocations
        await self._cleanup_all_allocations()
        
        # Clear resource pools
        self._resource_pools.clear()
    
    @asynccontextmanager
    async def allocate_resources(
        self,
        execution_id: str,
        estimated_duration: float = 30.0,
        node_count: int = 1,
        resource_requirements: Optional[Dict[str, Any]] = None
    ) -> ResourceAllocation:
        """
        Allocate resources for an execution.
        
        Args:
            execution_id: Unique execution identifier
            estimated_duration: Estimated execution duration in seconds
            node_count: Number of nodes in the execution
            resource_requirements: Specific resource requirements
            
        Yields:
            ResourceAllocation instance
        """
        async with self._lock:
            # Check if allocation already exists
            if execution_id in self._active_allocations:
                yield self._active_allocations[execution_id]
                return
            
            # Calculate resource requirements
            required_resources = self._calculate_resource_requirements(
                estimated_duration, node_count, resource_requirements
            )
            
            # Check resource availability
            if not self._check_resource_availability(required_resources):
                raise ResourceError("Insufficient resources available")
            
            # Create allocation
            allocation = ResourceAllocation(
                execution_id=execution_id,
                resource_limits=self._resource_limits,
                allocated_resources=required_resources,
                metadata={
                    "estimated_duration": estimated_duration,
                    "node_count": node_count,
                    "resource_requirements": resource_requirements,
                }
            )
            
            # Store allocation
            self._active_allocations[execution_id] = allocation
            self._metrics["allocations_created"] += 1
            
            # Emit allocation event
            await self._emit_event("resource_allocated", {
                "execution_id": execution_id,
                "allocation": allocation.to_dict(),
            })
            
            try:
                yield allocation
            finally:
                # Clean up allocation
                await self._cleanup_allocation(execution_id)
    
    def _calculate_resource_requirements(
        self,
        estimated_duration: float,
        node_count: int,
        resource_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[ResourceType, float]:
        """Calculate resource requirements for execution."""
        requirements = {
            ResourceType.CPU: 0.1 * node_count,  # 10% CPU per node
            ResourceType.MEMORY: 100.0 * node_count,  # 100MB memory per node
            ResourceType.NETWORK: 0.1 * node_count,  # 0.1 network connections per node
        }
        
        # Override with specific requirements if provided
        if resource_requirements:
            if "cpu_per_node" in resource_requirements:
                requirements[ResourceType.CPU] = resource_requirements["cpu_per_node"] * node_count
            if "memory_per_node" in resource_requirements:
                requirements[ResourceType.MEMORY] = resource_requirements["memory_per_node"] * node_count
            if "network_connections" in resource_requirements:
                requirements[ResourceType.NETWORK] = resource_requirements["network_connections"]
        
        # Scale by estimated duration
        duration_factor = min(estimated_duration / 30.0, 2.0)  # Scale up to 2x for longer executions
        for resource_type in requirements:
            requirements[resource_type] *= duration_factor
        
        return requirements
    
    def _check_resource_availability(self, required_resources: Dict[ResourceType, float]) -> bool:
        """Check if required resources are available."""
        current_usage = self._get_current_resource_usage()
        
        for resource_type, required_amount in required_resources.items():
            current = current_usage.get(resource_type, 0.0)
            limit = getattr(self._resource_limits, f"max_{resource_type.value}_usage")
            
            if current + required_amount > limit:
                return False
        
        return True
    
    def _get_current_resource_usage(self) -> Dict[ResourceType, float]:
        """Get current system resource usage."""
        try:
            cpu_percent = self._process.cpu_percent()
            memory_info = self._process.memory_info()
            disk_usage = self._process.disk_usage()
            
            return {
                ResourceType.CPU: cpu_percent,
                ResourceType.MEMORY: memory_info.percent,
                ResourceType.DISK: disk_usage.percent,
                ResourceType.NETWORK: len(self._process.connections()),
                ResourceType.GPU: 0.0,  # GPU monitoring would require additional setup
            }
        except Exception:
            return {
                ResourceType.CPU: 0.0,
                ResourceType.MEMORY: 0.0,
                ResourceType.DISK: 0.0,
                ResourceType.NETWORK: 0.0,
                ResourceType.GPU: 0.0,
            }
    
    async def _cleanup_allocation(self, execution_id: str) -> None:
        """Clean up resource allocation."""
        if execution_id in self._active_allocations:
            allocation = self._active_allocations[execution_id]
            allocation.end_time = datetime.now()
            allocation.status = "completed"
            
            # Update metrics
            self._metrics["allocations_completed"] += 1
            
            # Remove from active allocations
            del self._active_allocations[execution_id]
            
            # Emit cleanup event
            await self._emit_event("resource_deallocated", {
                "execution_id": execution_id,
                "allocation": allocation.to_dict(),
            })
    
    async def _cleanup_all_allocations(self) -> None:
        """Clean up all active allocations."""
        execution_ids = list(self._active_allocations.keys())
        for execution_id in execution_ids:
            await self._cleanup_allocation(execution_id)
    
    async def _monitor_system_resources(self) -> None:
        """Monitor system resources continuously."""
        while True:
            try:
                # Get current resource usage
                cpu_percent = self._process.cpu_percent()
                memory_info = self._process.memory_info()
                disk_usage = self._process.disk_usage()
                
                # Create resource usage records
                timestamp = datetime.now()
                
                for resource_type, usage in [
                    (ResourceType.CPU, cpu_percent),
                    (ResourceType.MEMORY, memory_info.percent),
                    (ResourceType.DISK, disk_usage.percent),
                    (ResourceType.NETWORK, len(self._process.connections())),
                ]:
                    usage_record = ResourceUsage(
                        resource_type=resource_type,
                        current_usage=usage,
                        peak_usage=0.0,
                        average_usage=0.0,
                        timestamp=timestamp,
                        process_id=self._process.pid,
                        metadata={}
                    )
                    
                    # Update peak usage
                    if resource_type in self._resource_pools:
                        pool = self._resource_pools[resource_type]
                        if pool:
                            pool.append(usage)
                            # Keep only last 100 records
                            if len(pool) > 100:
                                self._resource_pools[resource_type] = pool[-100:]
                    
                    # Add to history
                    self._resource_usage_history.append(usage_record)
                    # Keep only last 1000 records
                    if len(self._resource_usage_history) > 1000:
                        self._resource_usage_history = self._resource_usage_history[-1000:]
                
                await asyncio.sleep(self._monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Resource monitoring error: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _initialize_resource_pools(self) -> None:
        """Initialize resource pools for better performance."""
        # Pre-populate resource pools with current usage
        current_usage = self._get_current_resource_usage()
        
        for resource_type, usage in current_usage.items():
            self._resource_pools[resource_type] = [usage]
    
    async def _auto_scaling_loop(self) -> None:
        """Auto-scaling loop for resource management."""
        while True:
            try:
                # Check if auto-scaling is needed
                if self._needs_auto_scaling():
                    await self._perform_auto_scaling()
                
                await asyncio.sleep(5.0)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Auto-scaling error: {e}")
                await asyncio.sleep(5.0)
    
    def _needs_auto_scaling(self) -> bool:
        """Check if auto-scaling is needed."""
        current_usage = self._get_current_resource_usage()
        
        # Check if any resource is approaching limits
        for resource_type, usage in current_usage.items():
            limit = getattr(self._resource_limits, f"max_{resource_type.value}_usage")
            if usage > limit * 0.8:  # 80% threshold
                return True
        
        return False
    
    async def _perform_auto_scaling(self) -> None:
        """Perform auto-scaling actions."""
        current_usage = self._get_current_resource_usage()
        
        # Emit auto-scaling event
        self._metrics["auto_scaling_events"] += 1
        
        # Implementation would include:
        # - Scale up/down based on resource usage
        # - Adjust concurrent execution limits
        # - Trigger resource cleanup if needed
        pass
    
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
                print(f"Resource manager event handler error: {e}")
    
    def get_resource_usage(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        """Get resource usage information."""
        if execution_id and execution_id in self._active_allocations:
            allocation = self._get_allocation(execution_id)
            return {
                "allocation": allocation.to_dict(),
                "current_usage": self._get_current_resource_usage(),
                "resource_limits": self._resource_limits.to_dict(),
                "system_info": self._system_info,
            }
        
        return {
            "current_usage": self._get_current_resource_usage(),
            "resource_limits": self._resource_limits.to_dict(),
            "system_info": self._system_info,
            "active_allocations": len(self._active_allocations),
            "resource_pools": {
                resource_type.value: len(pool) 
                for resource_type, pool in self._resource_pools.items()
            },
            "metrics": self._metrics,
        }
    
    def _get_allocation(self, execution_id: str) -> Optional[ResourceAllocation]:
        """Get resource allocation by execution ID."""
        return self._active_allocations.get(execution_id)
    
    def get_available_resources(self) -> Dict[str, Any]:
        """Get available resources."""
        current_usage = self._get_current_resource_usage()
        available = {}
        
        for resource_type, limit in self._resource_limits.to_dict().items():
            current = current_usage.get(resource_type, 0.0)
            available[resource_type] = max(0, limit - current)
        
        return {
            "available_resources": available,
            "current_usage": current_usage,
            "resource_limits": self._resource_limits.to_dict(),
            "system_info": self._system_info,
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get resource manager metrics."""
        return self._metrics.copy()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            return {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total / (1024**3),  # GB
            "memory_available": psutil.virtual_memory().available / (1024**3),  # GB
            "disk_total": psutil.disk_usage('/').total / (1024**3),  # GB
            "disk_available": psutil.disk_usage('/').free / (1024**3),  # GB
            "platform": psutil.platform.system(),
            "python_version": psutil.sys.version,
            "process_count": len(psutil.pids()),
        }
        except Exception as e:
            return {
                "error": str(e),
                "platform": "unknown",
                "python_version": "unknown",
            }


class ResourceError(Exception):
    """Resource management related errors."""
    pass


# Global resource manager instance
_default_resource_manager = None


def get_default_resource_manager() -> ResourceManager:
    """Get the default resource manager instance."""
    global _default_resource_manager
    if _default_resource_manager is None:
        _default_resource_manager = ResourceManager()
    return _default_resource_manager


@asynccontextmanager
async def allocate_resources(
    execution_id: str,
    estimated_duration: float = 30.0,
    node_count: int = 1,
    resource_requirements: Optional[Dict[str, Any]] = None,
    manager: Optional[ResourceManager] = None
) -> ResourceAllocation:
    """
    Convenience function to allocate resources.
    
    Args:
        execution_id: Unique execution identifier
        estimated_duration: Estimated execution duration in seconds
        node_count: Number of nodes in the execution
        resource_requirements: Specific resource requirements
        manager: Custom resource manager instance
        
    Yields:
        ResourceAllocation instance
    """
    if manager is None:
        manager = get_default_resource_manager()
    
    async with manager.allocate_resources(
        execution_id=execution_id,
        estimated_duration=estimated_duration,
        node_count=node_count,
        resource_requirements=resource_requirements
    ) as allocation:
        yield allocation


async def get_resource_usage(
    execution_id: Optional[str] = None,
    manager: Optional[ResourceManager] = None
) -> Dict[str, Any]:
    """
    Convenience function to get resource usage.
    
    Args:
        execution_id: Execution ID (None for system-wide usage)
        manager: Custom resource manager instance
        
    Returns:
        Resource usage information
    """
    if manager is None:
        manager = get_default_resource_manager()
    
    return await manager.get_resource_usage(execution_id)