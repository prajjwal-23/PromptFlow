"""
Execution Repository Implementation

This module provides the concrete implementation of the ExecutionRepository
interface using SQLAlchemy for database operations.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import logging

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.execution.models import Execution, ExecutionStatus
from app.domain.execution.repositories import ExecutionRepository
from app.models.run import Run as RunModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionRepositoryImpl(ExecutionRepository):
    """Concrete implementation of ExecutionRepository using SQLAlchemy."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.logger = logger
    
    async def get_by_id(self, execution_id: str) -> Optional[Execution]:
        """Retrieve an execution by its ID."""
        try:
            # Query the database model
            stmt = select(RunModel).where(RunModel.id == execution_id)
            result = await self.session.execute(stmt)
            run_model = result.scalar_one_or_none()
            
            if run_model is None:
                return None
            
            # Convert to domain model
            return self._model_to_domain(run_model)
            
        except Exception as e:
            self.logger.error(f"Error getting execution by ID {execution_id}: {e}")
            raise
    
    async def save(self, execution: Execution) -> Execution:
        """Save an execution entity."""
        try:
            # Check if execution exists
            existing = await self.get_by_id(execution.id)
            
            if existing:
                # Update existing execution
                run_model = await self._domain_to_model(execution)
                run_model.updated_at = datetime.now(timezone.utc)
                
                # Update the model in database
                stmt = (
                    update(RunModel)
                    .where(RunModel.id == execution.id)
                    .values(
                        status=execution.status.value,
                        input_data=execution.input_data.inputs,
                        output_data=self._extract_outputs(execution),
                        error_message=execution.error,
                        metrics=execution.metrics.to_dict(),
                        started_at=execution.started_at,
                        completed_at=execution.completed_at,
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                await self.session.execute(stmt)
                
            else:
                # Create new execution
                run_model = await self._domain_to_model(execution)
                self.session.add(run_model)
            
            await self.session.flush()
            return execution
            
        except Exception as e:
            self.logger.error(f"Error saving execution {execution.id}: {e}")
            await self.session.rollback()
            raise
    
    async def delete(self, execution_id: str) -> bool:
        """Delete an execution by its ID."""
        try:
            stmt = delete(RunModel).where(RunModel.id == execution_id)
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting execution {execution_id}: {e}")
            await self.session.rollback()
            raise
    
    async def find_by_agent_id(self, agent_id: str) -> List[Execution]:
        """Find all executions for a specific agent."""
        try:
            stmt = (
                select(RunModel)
                .where(RunModel.agent_id == agent_id)
                .order_by(RunModel.created_at.desc())
            )
            result = await self.session.execute(stmt)
            run_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in run_models]
            
        except Exception as e:
            self.logger.error(f"Error finding executions for agent {agent_id}: {e}")
            raise
    
    async def find_by_status(self, status: ExecutionStatus) -> List[Execution]:
        """Find all executions with a specific status."""
        try:
            stmt = (
                select(RunModel)
                .where(RunModel.status == status.value)
                .order_by(RunModel.created_at.desc())
            )
            result = await self.session.execute(stmt)
            run_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in run_models]
            
        except Exception as e:
            self.logger.error(f"Error finding executions with status {status}: {e}")
            raise
    
    async def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Execution]:
        """Find executions within a date range."""
        try:
            stmt = (
                select(RunModel)
                .where(
                    and_(
                        RunModel.created_at >= start_date,
                        RunModel.created_at <= end_date
                    )
                )
                .order_by(RunModel.created_at.desc())
            )
            result = await self.session.execute(stmt)
            run_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in run_models]
            
        except Exception as e:
            self.logger.error(f"Error finding executions in date range: {e}")
            raise
    
    async def find_active_executions(self) -> List[Execution]:
        """Find all currently running executions."""
        try:
            active_statuses = [ExecutionStatus.RUNNING.value, ExecutionStatus.PENDING.value]
            stmt = (
                select(RunModel)
                .where(RunModel.status.in_(active_statuses))
                .order_by(RunModel.created_at.desc())
            )
            result = await self.session.execute(stmt)
            run_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in run_models]
            
        except Exception as e:
            self.logger.error(f"Error finding active executions: {e}")
            raise
    
    async def get_execution_count(self) -> int:
        """Get total count of executions."""
        try:
            stmt = select(func.count(RunModel.id))
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            self.logger.error(f"Error getting execution count: {e}")
            raise
    
    async def get_metrics_summary(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get execution metrics summary."""
        try:
            # Base query
            base_query = select(RunModel)
            
            # Apply date filters if provided
            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append(RunModel.created_at >= start_date)
                if end_date:
                    conditions.append(RunModel.created_at <= end_date)
                if conditions:
                    base_query = base_query.where(and_(*conditions))
            
            # Get counts by status
            status_counts = {}
            for status in ExecutionStatus:
                stmt = base_query.add_columns(
                    func.count(RunModel.id)
                ).where(RunModel.status == status.value)
                result = await self.session.execute(stmt)
                count = result.scalar() or 0
                status_counts[status.value] = count
            
            # Get total executions
            total_stmt = base_query.add_columns(func.count(RunModel.id))
            total_result = await self.session.execute(total_stmt)
            total_executions = total_result.scalar() or 0
            
            # Calculate success rate
            completed = status_counts.get(ExecutionStatus.COMPLETED.value, 0)
            failed = status_counts.get(ExecutionStatus.FAILED.value, 0)
            success_rate = (completed / total_executions * 100) if total_executions > 0 else 0
            
            # Get average execution time for completed executions
            avg_time_stmt = (
                base_query.add_columns(
                    func.avg(
                        func.extract('epoch', RunModel.completed_at) - 
                        func.extract('epoch', RunModel.started_at)
                    )
                )
                .where(
                    and_(
                        RunModel.status == ExecutionStatus.COMPLETED.value,
                        RunModel.started_at.isnot(None),
                        RunModel.completed_at.isnot(None)
                    )
                )
            )
            avg_time_result = await self.session.execute(avg_time_stmt)
            avg_execution_time = avg_time_result.scalar() or 0
            
            return {
                "total_executions": total_executions,
                "status_counts": status_counts,
                "success_rate": round(success_rate, 2),
                "average_execution_time": round(avg_execution_time, 2),
                "completed": completed,
                "failed": failed,
                "running": status_counts.get(ExecutionStatus.RUNNING.value, 0),
                "pending": status_counts.get(ExecutionStatus.PENDING.value, 0),
                "cancelled": status_counts.get(ExecutionStatus.CANCELLED.value, 0),
                "timeout": status_counts.get(ExecutionStatus.TIMEOUT.value, 0),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {e}")
            raise
    
    def _model_to_domain(self, model: RunModel) -> Execution:
        """Convert database model to domain model."""
        try:
            from app.domain.execution.models import (
                ExecutionInput, 
                ExecutionConfig, 
                ExecutionMetrics,
                NodeConfiguration,
                NodeOutput,
                NodeStatus,
                ResourceRequirement
            )
            
            # Create execution input
            input_data = ExecutionInput(
                inputs=model.input_data or {},
                context={},
                metadata={}
            )
            
            # Create execution config
            config = ExecutionConfig()
            
            # Create execution metrics
            metrics_dict = model.metrics or {}
            metrics = ExecutionMetrics(
                total_nodes=metrics_dict.get("total_nodes", 0),
                completed_nodes=metrics_dict.get("completed_nodes", 0),
                failed_nodes=metrics_dict.get("failed_nodes", 0),
                skipped_nodes=metrics_dict.get("skipped_nodes", 0),
                total_execution_time=metrics_dict.get("total_execution_time", 0.0),
                total_tokens_used=metrics_dict.get("total_tokens_used", 0),
                peak_memory_usage=metrics_dict.get("peak_memory_usage", 0),
                peak_cpu_usage=metrics_dict.get("peak_cpu_usage", 0.0),
                network_requests=metrics_dict.get("network_requests", 0),
            )
            
            # Create execution
            execution = Execution(
                id=model.id,
                agent_id=model.agent_id,
                status=ExecutionStatus(model.status),
                input_data=input_data,
                config=config,
                metrics=metrics,
                created_at=model.created_at.replace(tzinfo=timezone.utc),
                started_at=model.started_at.replace(tzinfo=timezone.utc) if model.started_at else None,
                completed_at=model.completed_at.replace(tzinfo=timezone.utc) if model.completed_at else None,
                error=model.error_message
            )
            
            return execution
            
        except Exception as e:
            self.logger.error(f"Error converting model to domain: {e}")
            raise
    
    async def _domain_to_model(self, execution: Execution) -> RunModel:
        """Convert domain model to database model."""
        try:
            # Create or update the database model
            model = RunModel(
                id=execution.id,
                agent_id=execution.agent_id,
                status=execution.status.value,
                input_data=execution.input_data.inputs,
                output_data=self._extract_outputs(execution),
                error_message=execution.error,
                metrics=execution.metrics.to_dict(),
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                created_at=execution.created_at,
                updated_at=datetime.now(timezone.utc)
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error converting domain to model: {e}")
            raise
    
    def _extract_outputs(self, execution: Execution) -> Optional[Dict[str, Any]]:
        """Extract outputs from execution for storage."""
        try:
            if not execution.node_outputs:
                return None
            
            outputs = {}
            for node_id, node_output in execution.node_outputs.items():
                outputs[node_id] = {
                    "status": node_output.status.value,
                    "data": node_output.data,
                    "error": node_output.error,
                    "execution_time": node_output.execution_time,
                    "tokens_used": node_output.tokens_used,
                    "metadata": node_output.metadata,
                    "timestamp": node_output.timestamp.isoformat(),
                }
            
            return outputs
            
        except Exception as e:
            self.logger.error(f"Error extracting outputs: {e}")
            return None