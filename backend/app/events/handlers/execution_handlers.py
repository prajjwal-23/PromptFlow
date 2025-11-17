"""
Execution Event Handlers

This module provides event handlers for execution-related events
with enterprise-grade patterns including async processing, error handling,
and performance monitoring.
"""

from __future__ import annotations
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import uuid

from ...domain.execution.models import (
    ExecutionEvent, 
    EventType, 
    ExecutionStatus, 
    NodeStatus,
    ExecutionMetrics,
    ExecutionStarted,
    ExecutionCompleted,
    NodeExecutionCompleted
)
from ...core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HandlerConfig:
    """Configuration for event handlers."""
    enabled: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    batch_size: int = 100
    enable_metrics: bool = True
    enable_tracing: bool = True


class BaseEventHandler(ABC):
    """Abstract base class for event handlers."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize event handler."""
        self._config = config
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._metrics = {
            "events_processed": 0,
            "events_failed": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
        }
    
    @abstractmethod
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle an event."""
        pass
    
    async def handle_with_retry(self, event: ExecutionEvent) -> None:
        """Handle event with retry logic."""
        if not self._config.enabled:
            return
        
        start_time = datetime.now()
        
        for attempt in range(self._config.retry_attempts + 1):
            try:
                # Apply timeout
                await asyncio.wait_for(
                    self.handle(event),
                    timeout=self._config.timeout
                )
                
                # Update metrics
                processing_time = (datetime.now() - start_time).total_seconds()
                self._update_metrics(processing_time, success=True)
                
                self._logger.debug(f"Successfully handled event {event.event_id}")
                return
                
            except asyncio.TimeoutError:
                self._logger.warning(f"Timeout handling event {event.event_id} (attempt {attempt + 1})")
            except Exception as e:
                self._logger.error(f"Error handling event {event.event_id} (attempt {attempt + 1}): {e}")
                
                if attempt < self._config.retry_attempts:
                    await asyncio.sleep(self._config.retry_delay * (2 ** attempt))
                else:
                    # Update metrics
                    processing_time = (datetime.now() - start_time).total_seconds()
                    self._update_metrics(processing_time, success=False)
                    raise
    
    def _update_metrics(self, processing_time: float, success: bool) -> None:
        """Update handler metrics."""
        if not self._config.enable_metrics:
            return
        
        self._metrics["events_processed"] += 1
        if not success:
            self._metrics["events_failed"] += 1
        
        self._metrics["total_processing_time"] += processing_time
        self._metrics["average_processing_time"] = (
            self._metrics["total_processing_time"] / self._metrics["events_processed"]
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get handler metrics."""
        return self._metrics.copy()


class ExecutionEventHandler(BaseEventHandler):
    """Handler for execution-level events."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize execution event handler."""
        super().__init__(config)
        self._execution_states: Dict[str, Dict[str, Any]] = {}
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle execution event."""
        if event.event_type in [
            EventType.EXECUTION_STARTED,
            EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_FAILED,
            EventType.EXECUTION_CANCELLED
        ]:
            await self._handle_execution_lifecycle(event)
        elif event.event_type == EventType.RESOURCE_ALLOCATED:
            await self._handle_resource_allocation(event)
        elif event.event_type == EventType.RESOURCE_RELEASED:
            await self._handle_resource_release(event)
    
    async def _handle_execution_lifecycle(self, event: ExecutionEvent) -> None:
        """Handle execution lifecycle events."""
        execution_id = event.execution_id
        
        if execution_id not in self._execution_states:
            self._execution_states[execution_id] = {
                "status": ExecutionStatus.PENDING,
                "started_at": None,
                "completed_at": None,
                "events": [],
            }
        
        state = self._execution_states[execution_id]
        state["events"].append(event)
        
        if event.event_type == EventType.EXECUTION_STARTED:
            state["status"] = ExecutionStatus.RUNNING
            state["started_at"] = event.timestamp
            self._logger.info(f"Execution {execution_id} started")
            
        elif event.event_type == EventType.EXECUTION_COMPLETED:
            state["status"] = ExecutionStatus.COMPLETED
            state["completed_at"] = event.timestamp
            duration = (state["completed_at"] - state["started_at"]).total_seconds()
            self._logger.info(f"Execution {execution_id} completed in {duration:.2f}s")
            
        elif event.event_type == EventType.EXECUTION_FAILED:
            state["status"] = ExecutionStatus.FAILED
            state["completed_at"] = event.timestamp
            error_message = event.data.get("error", "Unknown error")
            self._logger.error(f"Execution {execution_id} failed: {error_message}")
            
        elif event.event_type == EventType.EXECUTION_CANCELLED:
            state["status"] = ExecutionStatus.CANCELLED
            state["completed_at"] = event.timestamp
            self._logger.info(f"Execution {execution_id} cancelled")
    
    async def _handle_resource_allocation(self, event: ExecutionEvent) -> None:
        """Handle resource allocation events."""
        resources = event.data.get("resources", {})
        self._logger.info(f"Resources allocated for execution {event.execution_id}: {resources}")
    
    async def _handle_resource_release(self, event: ExecutionEvent) -> None:
        """Handle resource release events."""
        resources = event.data.get("resources", {})
        self._logger.info(f"Resources released for execution {event.execution_id}: {resources}")
    
    def get_execution_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an execution."""
        return self._execution_states.get(execution_id)


class NodeEventHandler(BaseEventHandler):
    """Handler for node-level events."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize node event handler."""
        super().__init__(config)
        self._node_states: Dict[str, Dict[str, Any]] = {}
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle node event."""
        if event.event_type in [
            EventType.NODE_STARTED,
            EventType.NODE_COMPLETED,
            EventType.NODE_FAILED,
            EventType.NODE_SKIPPED
        ]:
            await self._handle_node_lifecycle(event)
        elif event.event_type == EventType.TOKEN_STREAM:
            await self._handle_token_stream(event)
    
    async def _handle_node_lifecycle(self, event: ExecutionEvent) -> None:
        """Handle node lifecycle events."""
        node_id = event.node_id
        execution_id = event.execution_id
        
        if node_id not in self._node_states:
            self._node_states[node_id] = {
                "execution_id": execution_id,
                "status": NodeStatus.PENDING,
                "started_at": None,
                "completed_at": None,
                "events": [],
            }
        
        state = self._node_states[node_id]
        state["events"].append(event)
        
        if event.event_type == EventType.NODE_STARTED:
            state["status"] = NodeStatus.RUNNING
            state["started_at"] = event.timestamp
            self._logger.debug(f"Node {node_id} started in execution {execution_id}")
            
        elif event.event_type == EventType.NODE_COMPLETED:
            state["status"] = NodeStatus.COMPLETED
            state["completed_at"] = event.timestamp
            duration = (state["completed_at"] - state["started_at"]).total_seconds()
            self._logger.debug(f"Node {node_id} completed in {duration:.2f}s")
            
        elif event.event_type == EventType.NODE_FAILED:
            state["status"] = NodeStatus.FAILED
            state["completed_at"] = event.timestamp
            error_message = event.data.get("error", "Unknown error")
            self._logger.error(f"Node {node_id} failed: {error_message}")
            
        elif event.event_type == EventType.NODE_SKIPPED:
            state["status"] = NodeStatus.SKIPPED
            state["completed_at"] = event.timestamp
            reason = event.data.get("reason", "Unknown reason")
            self._logger.info(f"Node {node_id} skipped: {reason}")
    
    async def _handle_token_stream(self, event: ExecutionEvent) -> None:
        """Handle token stream events."""
        token_data = event.data.get("token", "")
        self._logger.debug(f"Token stream for node {event.node_id}: {token_data[:50]}...")
    
    def get_node_state(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a node."""
        return self._node_states.get(node_id)


class MetricsEventHandler(BaseEventHandler):
    """Handler for metrics collection and aggregation."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize metrics event handler."""
        super().__init__(config)
        self._execution_metrics: Dict[str, ExecutionMetrics] = {}
        self._global_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_nodes": 0,
            "successful_nodes": 0,
            "failed_nodes": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
        }
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle metrics-related events."""
        execution_id = event.execution_id
        
        # Initialize metrics if needed
        if execution_id not in self._execution_metrics:
            self._execution_metrics[execution_id] = ExecutionMetrics()
        
        metrics = self._execution_metrics[execution_id]
        
        if event.event_type == EventType.EXECUTION_STARTED:
            self._global_metrics["total_executions"] += 1
            
        elif event.event_type == EventType.EXECUTION_COMPLETED:
            self._global_metrics["successful_executions"] += 1
            await self._finalize_execution_metrics(execution_id)
            
        elif event.event_type == EventType.EXECUTION_FAILED:
            self._global_metrics["failed_executions"] += 1
            await self._finalize_execution_metrics(execution_id)
            
        elif event.event_type == EventType.NODE_STARTED:
            metrics.total_nodes += 1
            self._global_metrics["total_nodes"] += 1
            
        elif event.event_type == EventType.NODE_COMPLETED:
            metrics.completed_nodes += 1
            self._global_metrics["successful_nodes"] += 1
            
            # Update execution time
            execution_time = event.data.get("execution_time", 0.0)
            metrics.total_execution_time += execution_time
            self._global_metrics["total_execution_time"] += execution_time
            
        elif event.event_type == EventType.NODE_FAILED:
            metrics.failed_nodes += 1
            self._global_metrics["failed_nodes"] += 1
    
    async def _finalize_execution_metrics(self, execution_id: str) -> None:
        """Finalize metrics for a completed execution."""
        metrics = self._execution_metrics[execution_id]
        
        # Update global averages
        total_executions = (
            self._global_metrics["successful_executions"] + 
            self._global_metrics["failed_executions"]
        )
        
        if total_executions > 0:
            self._global_metrics["average_execution_time"] = (
                self._global_metrics["total_execution_time"] / total_executions
            )
    
    def get_execution_metrics(self, execution_id: str) -> Optional[ExecutionMetrics]:
        """Get metrics for a specific execution."""
        return self._execution_metrics.get(execution_id)
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global metrics."""
        return self._global_metrics.copy()


class NotificationEventHandler(BaseEventHandler):
    """Handler for sending notifications based on events."""
    
    def __init__(self, config: HandlerConfig):
        """Initialize notification event handler."""
        super().__init__(config)
        self._notification_channels: List[Callable] = []
    
    def add_notification_channel(self, channel: Callable) -> None:
        """Add a notification channel."""
        self._notification_channels.append(channel)
    
    async def handle(self, event: ExecutionEvent) -> None:
        """Handle notification events."""
        # Send notifications for important events
        if event.event_type in [
            EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_FAILED,
            EventType.ERROR_OCCURRED
        ]:
            await self._send_notification(event)
    
    async def _send_notification(self, event: ExecutionEvent) -> None:
        """Send notification through all channels."""
        notification_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "execution_id": event.execution_id,
            "node_id": event.node_id,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data,
            "metadata": event.metadata,
        }
        
        for channel in self._notification_channels:
            try:
                if asyncio.iscoroutinefunction(channel):
                    await channel(notification_data)
                else:
                    channel(notification_data)
            except Exception as e:
                self._logger.error(f"Failed to send notification through channel: {e}")


# Factory function for creating handlers
def create_execution_handlers(config: HandlerConfig) -> List[BaseEventHandler]:
    """Create all execution event handlers."""
    return [
        ExecutionEventHandler(config),
        NodeEventHandler(config),
        MetricsEventHandler(config),
        NotificationEventHandler(config),
    ]