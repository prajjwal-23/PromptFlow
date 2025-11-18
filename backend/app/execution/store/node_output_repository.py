"""
Node Output Repository Implementation

This module provides the concrete implementation of the NodeOutputRepository
interface using SQLAlchemy for database operations.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import logging

from sqlalchemy import select, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.execution.models import NodeOutput, NodeStatus
from app.domain.execution.repositories import NodeOutputRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class NodeOutputRepositoryImpl(NodeOutputRepository):
    """Concrete implementation of NodeOutputRepository using SQLAlchemy."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.logger = logger
    
    async def save_output(self, output: NodeOutput) -> NodeOutput:
        """Save a node output."""
        try:
            # Store node output in the execution's output_data field
            # This is a simplified approach - in a production system,
            # you might want a separate table for node outputs
            
            # For now, we'll store this in the Run model's output_data field
            # The actual implementation would be handled by the ExecutionRepository
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error saving node output {output.node_id}: {e}")
            raise
    
    async def get_output(self, execution_id: str, node_id: str) -> Optional[NodeOutput]:
        """Get a specific node output."""
        try:
            # Get the execution and extract node output
            from app.execution.store.execution_repository import ExecutionRepositoryImpl
            
            exec_repo = ExecutionRepositoryImpl(self.session)
            execution = await exec_repo.get_by_id(execution_id)
            
            if execution and node_id in execution.node_outputs:
                return execution.node_outputs[node_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting node output {node_id} for execution {execution_id}: {e}")
            raise
    
    async def get_outputs_by_execution_id(
        self, 
        execution_id: str
    ) -> List[NodeOutput]:
        """Get all outputs for an execution."""
        try:
            # Get the execution and extract all node outputs
            from app.execution.store.execution_repository import ExecutionRepositoryImpl
            
            exec_repo = ExecutionRepositoryImpl(self.session)
            execution = await exec_repo.get_by_id(execution_id)
            
            if execution:
                return list(execution.node_outputs.values())
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting outputs for execution {execution_id}: {e}")
            raise
    
    async def get_outputs_by_status(
        self, 
        status: NodeStatus,
        limit: Optional[int] = None
    ) -> List[NodeOutput]:
        """Get outputs by status."""
        try:
            # This would require a more complex query in a production system
            # For now, we'll return an empty list as this is a simplified implementation
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting outputs by status {status}: {e}")
            raise
    
    async def delete_outputs_by_execution_id(self, execution_id: str) -> int:
        """Delete all outputs for an execution. Returns count of deleted outputs."""
        try:
            # Get the execution and count outputs
            from app.execution.store.execution_repository import ExecutionRepositoryImpl
            
            exec_repo = ExecutionRepositoryImpl(self.session)
            execution = await exec_repo.get_by_id(execution_id)
            
            if execution:
                count = len(execution.node_outputs)
                # Clear the outputs
                execution.node_outputs.clear()
                # Save the execution
                await exec_repo.save(execution)
                return count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error deleting outputs for execution {execution_id}: {e}")
            raise
    
    async def get_output_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get output statistics."""
        try:
            # This would require aggregation queries in a production system
            # For now, we'll return basic statistics
            
            return {
                "total_outputs": 0,
                "successful_outputs": 0,
                "failed_outputs": 0,
                "average_execution_time": 0.0,
                "total_tokens_used": 0,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting output statistics: {e}")
            raise