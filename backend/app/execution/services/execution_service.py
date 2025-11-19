"""
Execution Service Implementation

This module provides the concrete implementation of the ExecutionService
interface for managing agent executions with enterprise-grade patterns.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
import logging

from app.domain.execution.models import (
    Execution,
    ExecutionStatus,
    ExecutionInput,
    ExecutionConfig,
    ExecutionMetrics,
    ExecutionEvent,
    NodeOutput,
    NodeStatus
)
from app.domain.execution.services import ExecutionService
from app.domain.execution.repositories import (
    ExecutionRepository,
    EventRepository,
    UnitOfWork
)
from app.execution.store.unit_of_work import unit_of_work_context
from app.execution.store.factory import create_repository_provider
from app.events.bus import get_event_bus
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionServiceImpl(ExecutionService):
    """Concrete implementation of ExecutionService."""
    
    def __init__(self, repository_provider=None):
        """Initialize execution service."""
        self.logger = logger
        self.repository_provider = repository_provider or create_repository_provider()
        self.event_bus = get_event_bus()
    
    async def create_execution(
        self,
        agent_id: str,
        input_data: ExecutionInput,
        config: Optional[ExecutionConfig] = None
    ) -> Execution:
        """Create a new execution."""
        try:
            # Validate inputs
            if not agent_id or not agent_id.strip():
                raise ValueError("Agent ID is required")
            
            if input_data is None:
                input_data = ExecutionInput()
            
            if config is None:
                config = ExecutionConfig()
            
            # Create execution
            execution = Execution(
                id=str(uuid4()),
                agent_id=agent_id,
                input_data=input_data,
                config=config
            )
            
            # Save execution
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                saved_execution = await execution_repo.save(execution)
                
                # Emit execution created event
                await self.event_bus.emit(
                    ExecutionEvent(
                        event_type=EventType.EXECUTION_STARTED,
                        execution_id=saved_execution.id,
                        data={"agent_id": agent_id, "input_data": input_data.inputs}
                    )
                )
                
                self.logger.info(f"Created execution {saved_execution.id} for agent {agent_id}")
                return saved_execution
                
        except Exception as e:
            self.logger.error(f"Error creating execution for agent {agent_id}: {e}")
            raise
    
    async def start_execution(self, execution_id: str) -> Execution:
        """Start an execution."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                event_repo = uow.get_event_repository()
                
                # Get execution
                execution = await execution_repo.get_by_id(execution_id)
                if execution is None:
                    raise ValueError(f"Execution {execution_id} not found")
                
                # Check if execution can be started
                if execution.status != ExecutionStatus.PENDING:
                    raise ValueError(f"Execution {execution_id} is not in pending status")
                
                # Update execution status
                execution.status = ExecutionStatus.RUNNING
                execution.started_at = datetime.now(timezone.utc)
                
                # Save execution
                saved_execution = await execution_repo.save(execution)
                
                # Create and save event
                start_event = ExecutionEvent(
                    event_type="execution_started",
                    execution_id=execution_id,
                    data={"started_at": execution.started_at.isoformat()}
                )
                await event_repo.save_event(start_event)
                
                # Emit event
                await self.event_bus.emit(start_event)
                
                self.logger.info(f"Started execution {execution_id}")
                return saved_execution
                
        except Exception as e:
            self.logger.error(f"Error starting execution {execution_id}: {e}")
            raise
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an execution."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                event_repo = uow.get_event_repository()
                
                # Get execution
                execution = await execution_repo.get_by_id(execution_id)
                if execution is None:
                    raise ValueError(f"Execution {execution_id} not found")
                
                # Check if execution can be cancelled
                if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                    return False
                
                # Update execution status
                execution.status = ExecutionStatus.CANCELLED
                execution.completed_at = datetime.now(timezone.utc)
                
                # Save execution
                await execution_repo.save(execution)
                
                # Create and save event
                cancel_event = ExecutionEvent(
                    event_type="execution_cancelled",
                    execution_id=execution_id,
                    data={"cancelled_at": execution.completed_at.isoformat()}
                )
                await event_repo.save_event(cancel_event)
                
                # Emit event
                await self.event_bus.emit(cancel_event)
                
                self.logger.info(f"Cancelled execution {execution_id}")
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                return await execution_repo.get_by_id(execution_id)
                
        except Exception as e:
            self.logger.error(f"Error getting execution {execution_id}: {e}")
            raise
    
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause an execution."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                event_repo = uow.get_event_repository()
                
                # Get execution
                execution = await execution_repo.get_by_id(execution_id)
                if execution is None:
                    raise ValueError(f"Execution {execution_id} not found")
                
                # Check if execution can be paused
                if execution.status != ExecutionStatus.RUNNING:
                    return False
                
                # Update execution status
                execution.status = ExecutionStatus.PAUSED
                
                # Save execution
                await execution_repo.save(execution)
                
                # Create and save event
                pause_event = ExecutionEvent(
                    event_type="execution_paused",
                    execution_id=execution_id,
                    data={"paused_at": datetime.now(timezone.utc).isoformat()}
                )
                await event_repo.save_event(pause_event)
                
                # Emit event
                await self.event_bus.emit(pause_event)
                
                self.logger.info(f"Paused execution {execution_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error pausing execution {execution_id}: {e}")
            raise
    
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                event_repo = uow.get_event_repository()
                
                # Get execution
                execution = await execution_repo.get_by_id(execution_id)
                if execution is None:
                    raise ValueError(f"Execution {execution_id} not found")
                
                # Check if execution can be resumed
                if execution.status != ExecutionStatus.PAUSED:
                    return False
                
                # Update execution status
                execution.status = ExecutionStatus.RUNNING
                
                # Save execution
                await execution_repo.save(execution)
                
                # Create and save event
                resume_event = ExecutionEvent(
                    event_type="execution_resumed",
                    execution_id=execution_id,
                    data={"resumed_at": datetime.now(timezone.utc).isoformat()}
                )
                await event_repo.save_event(resume_event)
                
                # Emit event
                await self.event_bus.emit(resume_event)
                
                self.logger.info(f"Resumed execution {execution_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error resuming execution {execution_id}: {e}")
            raise
    
    async def get_execution_pause_info(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get pause information for an execution."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                event_repo = uow.get_event_repository()
                
                # Get execution
                execution = await execution_repo.get_by_id(execution_id)
                if execution is None:
                    return None
                
                # Check if execution is paused
                if execution.status != ExecutionStatus.PAUSED:
                    return None
                
                # Get pause event
                pause_events = await event_repo.get_events_by_execution_id(
                    execution_id,
                    event_type="execution_paused",
                    limit=1
                )
                
                if not pause_events:
                    return None
                
                pause_event = pause_events[0]
                paused_at = datetime.fromisoformat(pause_event.data.get("paused_at"))
                paused_duration = (datetime.now(timezone.utc) - paused_at).total_seconds()
                
                return {
                    "execution_id": execution_id,
                    "paused_at": paused_at.isoformat(),
                    "paused_duration_seconds": paused_duration,
                    "status": execution.status.value,
                    "can_resume": True
                }
                
        except Exception as e:
            self.logger.error(f"Error getting execution pause info {execution_id}: {e}")
            raise
    
    async def list_executions(
        self,
        agent_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Execution]:
        """List executions with optional filters."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                
                # Apply filters
                if agent_id and status:
                    # Both filters - need to combine results
                    agent_executions = await execution_repo.find_by_agent_id(agent_id)
                    status_executions = await execution_repo.find_by_status(status)
                    
                    # Find intersection
                    agent_ids = {exec.id for exec in agent_executions}
                    filtered_executions = [
                        exec for exec in status_executions 
                        if exec.id in agent_ids
                    ]
                elif agent_id:
                    filtered_executions = await execution_repo.find_by_agent_id(agent_id)
                elif status:
                    filtered_executions = await execution_repo.find_by_status(status)
                else:
                    # Get all executions (limited)
                    filtered_executions = await execution_repo.find_by_status(ExecutionStatus.PENDING)
                    filtered_executions.extend(await execution_repo.find_by_status(ExecutionStatus.RUNNING))
                    filtered_executions.extend(await execution_repo.find_by_status(ExecutionStatus.COMPLETED))
                    filtered_executions.extend(await execution_repo.find_by_status(ExecutionStatus.FAILED))
                    filtered_executions.extend(await execution_repo.find_by_status(ExecutionStatus.CANCELLED))
                
                # Sort by created_at descending
                filtered_executions.sort(key=lambda x: x.created_at, reverse=True)
                
                # Apply pagination
                if offset:
                    filtered_executions = filtered_executions[offset:]
                
                if limit:
                    filtered_executions = filtered_executions[:limit]
                
                return filtered_executions
                
        except Exception as e:
            self.logger.error(f"Error listing executions: {e}")
            raise
    
    async def get_execution_metrics(
        self,
        execution_id: str
    ) -> Optional[ExecutionMetrics]:
        """Get execution metrics."""
        try:
            execution = await self.get_execution(execution_id)
            if execution is None:
                return None
            
            # Update metrics based on current state
            execution.update_metrics()
            return execution.metrics
            
        except Exception as e:
            self.logger.error(f"Error getting execution metrics {execution_id}: {e}")
            raise
    
    async def complete_execution(
        self, 
        execution_id: str, 
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Execution:
        """Complete an execution with success or failure."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                event_repo = uow.get_event_repository()
                
                # Get execution
                execution = await execution_repo.get_by_id(execution_id)
                if execution is None:
                    raise ValueError(f"Execution {execution_id} not found")
                
                # Check if execution can be completed
                if execution.status not in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]:
                    raise ValueError(f"Execution {execution_id} is not in a completable state")
                
                # Update execution
                execution.completed_at = datetime.now(timezone.utc)
                
                if error:
                    execution.status = ExecutionStatus.FAILED
                    execution.error = error
                    event_type = EventType.EXECUTION_FAILED
                else:
                    execution.status = ExecutionStatus.COMPLETED
                    if output_data:
                        # Store output data in node outputs
                        from app.domain.execution.models import NodeOutput, NodeStatus
                        output_node = NodeOutput(
                            node_id="output",
                            status=NodeStatus.COMPLETED,
                            data=output_data
                        )
                        execution.set_node_output(output_node)
                    event_type = EventType.EXECUTION_COMPLETED
                
                # Update metrics
                execution.update_metrics()
                
                # Save execution
                saved_execution = await execution_repo.save(execution)
                
                # Create and save event
                complete_event = ExecutionEvent(
                    event_type=event_type,
                    execution_id=execution_id,
                    data={
                        "completed_at": execution.completed_at.isoformat(),
                        "metrics": execution.metrics.to_dict(),
                        "error": error
                    }
                )
                await event_repo.save_event(complete_event)
                
                # Emit event
                await self.event_bus.emit(complete_event)
                
                status_text = "completed" if not error else "failed"
                self.logger.info(f"Execution {execution_id} {status_text}")
                return saved_execution
                
        except Exception as e:
            self.logger.error(f"Error completing execution {execution_id}: {e}")
            raise
    
    async def get_active_executions(self) -> List[Execution]:
        """Get all currently active executions."""
        try:
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                return await execution_repo.find_active_executions()
                
        except Exception as e:
            self.logger.error(f"Error getting active executions: {e}")
            raise
    
    async def cleanup_old_executions(self, cutoff_days: int = 30) -> int:
        """Clean up old executions."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=cutoff_days)
            
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                
                # Get old executions
                old_executions = await execution_repo.find_by_date_range(
                    start_date=datetime.min.replace(tzinfo=timezone.utc),
                    end_date=cutoff_date
                )
                
                # Delete old executions
                deleted_count = 0
                for execution in old_executions:
                    if await execution_repo.delete(execution.id):
                        deleted_count += 1
                
                self.logger.info(f"Cleaned up {deleted_count} old executions")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old executions: {e}")
            raise
    
    async def restart_execution(self, execution_id: str) -> Execution:
        """Restart an execution."""
        try:
            # Get original execution
            original_execution = await self.get_execution(execution_id)
            if original_execution is None:
                raise ValueError(f"Execution {execution_id} not found")
            
            # Create new execution with same data
            new_execution = await self.create_execution(
                agent_id=original_execution.agent_id,
                input_data=original_execution.input_data,
                config=original_execution.config
            )
            
            # Start new execution
            return await self.start_execution(new_execution.id)
            
        except Exception as e:
            self.logger.error(f"Error restarting execution {execution_id}: {e}")
            raise
    
    async def get_execution_history(self, execution_id: str) -> List[ExecutionEvent]:
        """Get execution event history."""
        try:
            async with unit_of_work_context() as uow:
                event_repo = uow.get_event_repository()
                return await event_repo.get_events_by_execution_id(execution_id)
                
        except Exception as e:
            self.logger.error(f"Error getting execution history {execution_id}: {e}")
            raise
    
    async def get_execution_statistics(
        self,
        agent_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get execution statistics."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)
            
            async with unit_of_work_context() as uow:
                execution_repo = uow.get_execution_repository()
                
                # Get executions in date range
                if agent_id:
                    executions = await execution_repo.find_by_agent_id(agent_id)
                    executions = [e for e in executions if e.created_at >= cutoff_date]
                else:
                    executions = await execution_repo.find_by_date_range(cutoff_date, datetime.now(timezone.utc))
                
                # Calculate statistics
                total = len(executions)
                completed = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
                failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
                cancelled = len([e for e in executions if e.status == ExecutionStatus.CANCELLED])
                running = len([e for e in executions if e.status == ExecutionStatus.RUNNING])
                pending = len([e for e in executions if e.status == ExecutionStatus.PENDING])
                
                # Calculate average execution time
                completed_executions = [e for e in executions if e.duration is not None]
                avg_duration = sum(e.duration for e in completed_executions) / len(completed_executions) if completed_executions else 0
                
                return {
                    "total_executions": total,
                    "completed": completed,
                    "failed": failed,
                    "cancelled": cancelled,
                    "running": running,
                    "pending": pending,
                    "success_rate": (completed / total * 100) if total > 0 else 0,
                    "average_duration_seconds": avg_duration,
                    "date_range": {
                        "start": cutoff_date.isoformat(),
                        "end": datetime.now(timezone.utc).isoformat()
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error getting execution statistics: {e}")
            raise
    
    async def validate_execution_config(self, config: ExecutionConfig) -> Dict[str, Any]:
        """Validate execution configuration."""
        try:
            validation_results = {
                "valid": True,
                "warnings": [],
                "errors": []
            }
            
            # Check timeout
            if config.timeout and config.timeout < 1:
                validation_results["errors"].append("Timeout must be at least 1 second")
                validation_results["valid"] = False
            
            # Check max retries
            if config.max_retries and config.max_retries < 0:
                validation_results["errors"].append("Max retries cannot be negative")
                validation_results["valid"] = False
            
            # Check memory limit
            if config.memory_limit_mb and config.memory_limit_mb < 64:
                validation_results["warnings"].append("Memory limit should be at least 64MB for optimal performance")
            
            # Check parallel execution
            if config.max_parallel_nodes and config.max_parallel_nodes > 10:
                validation_results["warnings"].append("High parallel node count may impact performance")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating execution config: {e}")
            raise
    
    async def clone_execution(self, execution_id: str) -> Execution:
        """Clone an execution with same configuration."""
        try:
            original_execution = await self.get_execution(execution_id)
            if original_execution is None:
                raise ValueError(f"Execution {execution_id} not found")
            
            # Create clone with modified metadata
            cloned_input = ExecutionInput(
                inputs=original_execution.input_data.inputs.copy(),
                metadata={
                    **original_execution.input_data.metadata,
                    "cloned_from": execution_id,
                    "cloned_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            cloned_execution = await self.create_execution(
                agent_id=original_execution.agent_id,
                input_data=cloned_input,
                config=original_execution.config
            )
            
            self.logger.info(f"Cloned execution {execution_id} to {cloned_execution.id}")
            return cloned_execution
            
        except Exception as e:
            self.logger.error(f"Error cloning execution {execution_id}: {e}")
            raise

# Factory function
def create_execution_service() -> ExecutionService:
    """Create execution service instance."""
    return ExecutionServiceImpl()