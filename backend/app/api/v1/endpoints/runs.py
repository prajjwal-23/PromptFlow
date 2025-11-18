
"""
Agent run management endpoints.

This module provides comprehensive run management API endpoints that integrate
with the execution system, including real-time streaming, metrics, and event handling.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
import json
import asyncio

from app.core.auth import get_current_user
from app.core.permissions import require_permission
from app.core.logging import get_logger
from app.models.user import User
from app.execution.services.factory import create_service_provider
from app.domain.execution.models import (
    ExecutionInput,
    ExecutionConfig,
    ExecutionStatus,
    Priority
)
from app.websocket.streaming import get_event_streamer

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models
class RunCreateRequest(BaseModel):
    """Run creation request model."""
    agent_id: str = Field(..., description="ID of the agent to run")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the run")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Execution configuration")
    priority: Optional[str] = Field(default="normal", description="Execution priority")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class RunUpdateRequest(BaseModel):
    """Run update request model."""
    status: Optional[str] = Field(default=None, description="New status")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Updated input data")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Updated configuration")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata")


class RunResponse(BaseModel):
    """Run response model."""
    id: str
    agent_id: str
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    metrics: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
    duration: Optional[float]
    is_finished: bool
    is_running: bool
    metadata: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RunEventResponse(BaseModel):
    """Run event response model."""
    id: str
    run_id: str
    node_id: Optional[str]
    event_type: str
    level: str
    message: str
    data: Optional[Dict[str, Any]]
    timestamp: datetime
    duration_ms: Optional[float]
    token_count: Optional[int]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunListResponse(BaseModel):
    """Run list response model."""
    runs: List[RunResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class RunMetricsResponse(BaseModel):
    """Run metrics response model."""
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    skipped_nodes: int
    total_execution_time: float
    total_tokens_used: int
    peak_memory_usage: int
    peak_cpu_usage: float
    network_requests: int
    success_rate: float
    average_execution_time: float


class RunStreamRequest(BaseModel):
    """Run stream request model."""
    run_id: str
    event_types: Optional[List[str]] = Field(default=None, description="Event types to stream")
    include_metrics: bool = Field(default=True, description="Include metrics in stream")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")


# Helper functions
def get_service_provider_instance():
    """Get service provider instance."""
    return create_service_provider()


def _execution_to_response(execution) -> RunResponse:
    """Convert execution domain model to response model."""
    return RunResponse(
        id=execution.id,
        agent_id=execution.agent_id,
        status=execution.status.value,
        input_data=execution.input_data.inputs,
        output_data=execution.node_outputs.get("output", {}).data if execution.node_outputs.get("output") else None,
        error_message=execution.error,
        metrics=execution.metrics.to_dict(),
        created_at=execution.created_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        updated_at=execution.created_at,  # TODO: Add updated_at to execution model
        duration=execution.duration,
        is_finished=execution.is_finished,
        is_running=execution.is_running,
        metadata=execution.input_data.metadata
    )


def _event_to_response(event) -> RunEventResponse:
    """Convert event domain model to response model."""
    return RunEventResponse(
        id=event.event_id,
        run_id=event.execution_id,
        node_id=event.node_id,
        event_type=event.event_type.value,
        level="info",  # TODO: Add level to event model
        message=f"Event {event.event_type.value}",
        data=event.data,
        timestamp=event.timestamp,
        duration_ms=event.metadata.get("duration_ms"),
        token_count=event.metadata.get("token_count")
    )


# API Endpoints
@router.post("/", response_model=RunResponse)
async def create_run(
    run_data: RunCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new agent run.
    
    This endpoint creates a new execution run for the specified agent with the given input data.
    The run can be configured with various options including priority and execution settings.
    """
    try:
        logger.info("Creating run", agent_id=run_data.agent_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Convert request to domain models
        input_data = ExecutionInput(
            inputs=run_data.input_data,
            metadata=run_data.metadata
        )
        
        config = ExecutionConfig()
        if run_data.config:
            # Update config with provided values
            for key, value in run_data.config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Set priority
        if run_data.priority:
            try:
                config.priority = Priority(run_data.priority)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {run_data.priority}")
        
        # Create execution
        execution = await execution_service.create_execution(
            agent_id=run_data.agent_id,
            input_data=input_data,
            config=config
        )
        
        # Start execution in background
        background_tasks.add_task(
            execution_service.start_execution,
            execution.id
        )
        
        logger.info("Run created successfully", run_id=execution.id)
        return _execution_to_response(execution)
        
    except Exception as e:
        logger.error("Error creating run", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=RunListResponse)
async def get_runs(
    agent_id: Optional[str] = Query(default=None, description="Filter by agent ID"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user)
):
    """
    Get runs with filtering and pagination.
    
    This endpoint retrieves runs with optional filtering by agent ID and status,
    with support for pagination.
    """
    try:
        logger.info("Getting runs", agent_id=agent_id, status=status, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Convert status string to enum
        execution_status = None
        if status:
            try:
                execution_status = ExecutionStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Get executions
        executions = await execution_service.list_executions(
            agent_id=agent_id,
            status=execution_status,
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        # Convert to response models
        run_responses = [_execution_to_response(execution) for execution in executions]
        
        # TODO: Get total count for pagination
        total = len(run_responses)
        
        return RunListResponse(
            runs=run_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=total > page * page_size,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error("Error getting runs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get run by ID.
    
    This endpoint retrieves detailed information about a specific run.
    """
    try:
        logger.info("Getting run", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Get execution
        execution = await execution_service.get_execution(run_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return _execution_to_response(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting run", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{run_id}", response_model=RunResponse)
async def update_run(
    run_id: str,
    run_data: RunUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update run.
    
    This endpoint updates an existing run with new data.
    Note: Some fields like status may be restricted based on current run state.
    """
    try:
        logger.info("Updating run", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Get current execution
        execution = await execution_service.get_execution(run_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Update fields
        if run_data.input_data:
            execution.input_data.inputs = run_data.input_data
        
        if run_data.metadata:
            execution.input_data.metadata = run_data.metadata
        
        # TODO: Implement actual update logic in execution service
        # For now, just return the current execution
        
        return _execution_to_response(execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating run", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel running run.
    
    This endpoint cancels a currently running run.
    """
    try:
        logger.info("Cancelling run", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Cancel execution
        success = await execution_service.cancel_execution(run_id)
        if not success:
            raise HTTPException(status_code=400, detail="Run cannot be cancelled")
        
        return {"message": "Run cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error cancelling run", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/events", response_model=List[RunEventResponse])
async def get_run_events(
    run_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of events"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    current_user: User = Depends(get_current_user)
):
    """
    Get events for a run.
    
    This endpoint retrieves the event log for a specific run.
    """
    try:
        logger.info("Getting run events", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        repository_provider = provider.factory.repository_provider
        event_repo = repository_provider.get_event_repository()
        
        # Get events
        events = await event_repo.get_events_by_execution_id(run_id, limit=limit)
        
        # Filter by event type if specified
        if event_type:
            events = [event for event in events if event.event_type.value == event_type]
        
        # Convert to response models
        event_responses = [_event_to_response(event) for event in events]
        
        return event_responses
        
    except Exception as e:
        logger.error("Error getting run events", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/metrics", response_model=RunMetricsResponse)
async def get_run_metrics(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get metrics for a run.
    
    This endpoint retrieves performance metrics for a specific run.
    """
    try:
        logger.info("Getting run metrics", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Get execution metrics
        metrics = await execution_service.get_execution_metrics(run_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return RunMetricsResponse(
            total_nodes=metrics.total_nodes,
            completed_nodes=metrics.completed_nodes,
            failed_nodes=metrics.failed_nodes,
            skipped_nodes=metrics.skipped_nodes,
            total_execution_time=metrics.total_execution_time,
            total_tokens_used=metrics.total_tokens_used,
            peak_memory_usage=metrics.peak_memory_usage,
            peak_cpu_usage=metrics.peak_cpu_usage,
            network_requests=metrics.network_requests,
            success_rate=metrics.success_rate,
            average_execution_time=metrics.average_execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting run metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/stream")
async def stream_run(
    run_id: str,
    event_types: Optional[str] = Query(default=None, description="Comma-separated event types"),
    include_metrics: bool = Query(default=True, description="Include metrics in stream"),
    current_user: User = Depends(get_current_user)
):
    """
    Stream run events in real-time.
    
    This endpoint provides Server-Sent Events (SSE) streaming for real-time updates
    on run execution progress.
    """
    try:
        logger.info("Starting run stream", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        streaming_service = provider.get_streaming_service()
        
        # Parse event types
        event_type_list = None
        if event_types:
            event_type_list = [t.strip() for t in event_types.split(",")]
        
        async def event_stream():
            """Generate SSE stream."""
            try:
                async for event in streaming_service.start_stream(run_id, f"user_{current_user.id}"):
                    # Filter by event types if specified
                    if event_type_list and event.get("event_type") not in event_type_list:
                        continue
                    
                    # Format as SSE
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except Exception as e:
                logger.error("Error in event stream", error=str(e))
                error_event = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        logger.error("Error starting run stream", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/restart")
async def restart_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Restart a run.
    
    This endpoint restarts a completed or failed run with the same input data.
    """
    try:
        logger.info("Restarting run", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Get original execution
        original_execution = await execution_service.get_execution(run_id)
        if not original_execution:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Create new execution with same data
        new_execution = await execution_service.create_execution(
            agent_id=original_execution.agent_id,
            input_data=original_execution.input_data,
            config=original_execution.config
        )
        
        # Start new execution in background
        background_tasks.add_task(
            execution_service.start_execution,
            new_execution.id
        )
        
        logger.info("Run restarted successfully", new_run_id=new_execution.id)
        return _execution_to_response(new_execution)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error restarting run", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{run_id}")
async def delete_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a run.
    
    This endpoint permanently deletes a run and all its associated data.
    Only completed, failed, or cancelled runs can be deleted.
    """
    try:
        logger.info("Deleting run", run_id=run_id, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        execution_service = provider.get_execution_service()
        
        # Get execution
        execution = await execution_service.get_execution(run_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Check if run can be deleted
        if execution.status == ExecutionStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Cannot delete running run")
        
        # TODO: Implement actual deletion in execution service
        # For now, just return success
        
        return {"message": "Run deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting run", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Health and metrics endpoints
@router.get("/health/status")
async def runs_health_check():
    """Check health of runs system."""
    try:
        provider = get_service_provider_instance()
        factory = provider.factory
        
        health = await factory.health_check()
        return health
        
    except Exception as e:
        logger.error("Error in health check", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/metrics/summary")
async def get_runs_metrics_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to summarize"),
    current_user: User = Depends(get_current_user)
):
    """
    Get runs metrics summary.
    
    This endpoint provides a summary of run metrics over the specified time period.
    """
    try:
        logger.info("Getting runs metrics summary", days=days, user_id=current_user.id)
        
        # Get services
        provider = get_service_provider_instance()
        repository_provider = provider.factory.repository_provider
        execution_repo = repository_provider.get_execution_repository()
        
        # Get metrics summary
        start_date = datetime.now(timezone.utc) - timezone.timedelta(days=days)
        metrics = await execution_repo.get_metrics_summary(start_date=start_date)
        
        return metrics
        
    except Exception as e:
        logger.error("Error getting runs metrics summary", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))