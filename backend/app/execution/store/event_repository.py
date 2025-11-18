"""
Event Repository Implementation

This module provides the concrete implementation of the EventRepository
interface using SQLAlchemy for database operations.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import logging

from sqlalchemy import select, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.execution.models import ExecutionEvent, EventType
from app.domain.execution.repositories import EventRepository
from app.models.run import RunEvent as RunEventModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class EventRepositoryImpl(EventRepository):
    """Concrete implementation of EventRepository using SQLAlchemy."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
        self.logger = logger
    
    async def save_event(self, event: ExecutionEvent) -> ExecutionEvent:
        """Save an execution event."""
        try:
            # Convert domain event to database model
            event_model = RunEventModel(
                id=event.event_id,
                run_id=event.execution_id,
                node_id=event.node_id,
                event_type=event.event_type.value,
                level="info",  # Default level, can be enhanced
                message=self._create_event_message(event),
                data=event.data,
                timestamp=event.timestamp,
                duration_ms=event.metadata.get("duration_ms"),
                token_count=event.metadata.get("token_count")
            )
            
            self.session.add(event_model)
            await self.session.flush()
            
            return event
            
        except Exception as e:
            self.logger.error(f"Error saving event {event.event_id}: {e}")
            await self.session.rollback()
            raise
    
    async def get_events_by_execution_id(
        self, 
        execution_id: str,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get all events for a specific execution."""
        try:
            stmt = (
                select(RunEventModel)
                .where(RunEventModel.run_id == execution_id)
                .order_by(RunEventModel.timestamp.asc())
            )
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            event_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in event_models]
            
        except Exception as e:
            self.logger.error(f"Error getting events for execution {execution_id}: {e}")
            raise
    
    async def get_events_by_type(
        self, 
        event_type: str,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get events by type."""
        try:
            stmt = (
                select(RunEventModel)
                .where(RunEventModel.event_type == event_type)
                .order_by(RunEventModel.timestamp.desc())
            )
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            event_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in event_models]
            
        except Exception as e:
            self.logger.error(f"Error getting events by type {event_type}: {e}")
            raise
    
    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None
    ) -> List[ExecutionEvent]:
        """Get events within a date range."""
        try:
            stmt = (
                select(RunEventModel)
                .where(
                    and_(
                        RunEventModel.timestamp >= start_date,
                        RunEventModel.timestamp <= end_date
                    )
                )
                .order_by(RunEventModel.timestamp.desc())
            )
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            event_models = result.scalars().all()
            
            return [self._model_to_domain(model) for model in event_models]
            
        except Exception as e:
            self.logger.error(f"Error getting events in date range: {e}")
            raise
    
    async def delete_old_events(
        self, 
        cutoff_date: datetime
    ) -> int:
        """Delete events older than cutoff date. Returns count of deleted events."""
        try:
            stmt = delete(RunEventModel).where(RunEventModel.timestamp < cutoff_date)
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount
            
        except Exception as e:
            self.logger.error(f"Error deleting old events: {e}")
            await self.session.rollback()
            raise
    
    async def get_event_count(self) -> int:
        """Get total count of events."""
        try:
            stmt = select(func.count(RunEventModel.id))
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            self.logger.error(f"Error getting event count: {e}")
            raise
    
    def _model_to_domain(self, model: RunEventModel) -> ExecutionEvent:
        """Convert database model to domain model."""
        try:
            # Convert event type string to enum
            event_type = EventType(model.event_type)
            
            # Create metadata from model fields
            metadata = {}
            if model.duration_ms is not None:
                metadata["duration_ms"] = model.duration_ms
            if model.token_count is not None:
                metadata["token_count"] = model.token_count
            
            # Create domain event
            event = ExecutionEvent(
                event_id=model.id,
                event_type=event_type,
                execution_id=model.run_id,
                node_id=model.node_id,
                timestamp=model.timestamp.replace(tzinfo=timezone.utc),
                data=model.data or {},
                metadata=metadata
            )
            
            return event
            
        except Exception as e:
            self.logger.error(f"Error converting model to domain: {e}")
            raise
    
    def _create_event_message(self, event: ExecutionEvent) -> str:
        """Create a descriptive message for the event."""
        try:
            # Create human-readable message based on event type
            messages = {
                EventType.EXECUTION_STARTED: f"Execution started for {event.execution_id}",
                EventType.EXECUTION_COMPLETED: f"Execution completed for {event.execution_id}",
                EventType.EXECUTION_FAILED: f"Execution failed for {event.execution_id}",
                EventType.EXECUTION_CANCELLED: f"Execution cancelled for {event.execution_id}",
                EventType.NODE_STARTED: f"Node {event.node_id} started",
                EventType.NODE_COMPLETED: f"Node {event.node_id} completed",
                EventType.NODE_FAILED: f"Node {event.node_id} failed",
                EventType.NODE_SKIPPED: f"Node {event.node_id} skipped",
                EventType.TOKEN_STREAM: f"Token stream for node {event.node_id}",
                EventType.ERROR_OCCURRED: f"Error occurred in execution {event.execution_id}",
                EventType.RESOURCE_ALLOCATED: f"Resources allocated for {event.execution_id}",
                EventType.RESOURCE_RELEASED: f"Resources released for {event.execution_id}",
            }
            
            return messages.get(event.event_type, f"Event {event.event_type.value} occurred")
            
        except Exception as e:
            self.logger.error(f"Error creating event message: {e}")
            return f"Event {event.event_type.value} occurred"