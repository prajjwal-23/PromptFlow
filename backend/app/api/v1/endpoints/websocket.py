"""
WebSocket endpoint for real-time execution streaming.

This module provides WebSocket endpoints for real-time communication
with clients during agent execution, including event streaming,
status updates, and interactive control.
"""

import json
import logging
from typing import Dict, Optional, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from starlette.status import WS_1000_NORMAL_CLOSURE, WS_1008_POLICY_VIOLATION

from app.core.auth import get_current_user_websocket
from app.core.permissions import require_workspace_permission
from app.models.user import User
from app.websocket.manager import WebSocketManager
from app.websocket.streaming import EventStreamer
from app.events.bus import EventBus
from app.events.store import EventStore
from app.execution.services.execution_service import ExecutionService
from app.core.database import get_db
from app.models.agent import Agent
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

# Global WebSocket manager instance (will be initialized on first use)
ws_manager: WebSocketManager = None
event_streamer: EventStreamer = None
event_bus: EventBus = None
event_store: EventStore = None
execution_service: ExecutionService = None

def get_websocket_components():
    """Get or initialize WebSocket components."""
    global ws_manager, event_streamer, event_bus, event_store, execution_service
    if ws_manager is None:
        ws_manager = WebSocketManager()
        event_streamer = EventStreamer(ws_manager)
        event_bus = EventBus()
        event_store = EventStore()
        execution_service = ExecutionService()
    return ws_manager, event_streamer, event_bus, event_store, execution_service


@router.websocket("/ws/{execution_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    execution_id: str,
    token: Optional[str] = Query(None),
    user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for real-time execution updates.
    
    Args:
        websocket: WebSocket connection instance
        execution_id: ID of the execution to stream
        token: Authentication token (optional, can be in query params)
        user: Authenticated user from dependency injection
    """
    try:
        # Get WebSocket components
        ws_mgr, event_strmr, event_bus, event_store, exec_svc = get_websocket_components()
        
        # Validate execution exists and user has access
        execution = await exec_svc.get_execution(execution_id)
        if not execution:
            await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Execution not found")
            return

        # Check workspace permissions
        await require_workspace_permission(user, execution.agent.workspace_id, "read")

        # Accept WebSocket connection
        await ws_mgr.connect(websocket, execution_id, user.id)
        logger.info(f"WebSocket connected for execution {execution_id} by user {user.id}")

        try:
            # Send initial execution status
            await send_initial_status(websocket, execution, event_store)

            # Subscribe to execution events
            await event_strmr.subscribe_to_execution(execution_id, websocket)

            # Keep connection alive and handle messages
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle client messages
                    await handle_client_message(websocket, execution_id, user, message)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for execution {execution_id}")
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client for execution {execution_id}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": "Invalid JSON format"}
                    }))
                except Exception as e:
                    logger.error(f"Error handling WebSocket message for execution {execution_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "data": {"message": "Internal server error"}
                    }))

        except WebSocketDisconnect:
            pass
        finally:
            # Clean up connection
            await ws_mgr.disconnect(websocket, execution_id)
            await event_strmr.unsubscribe_from_execution(execution_id, websocket)
            logger.info(f"WebSocket cleanup completed for execution {execution_id}")

    except HTTPException as e:
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason=str(e.detail))
    except Exception as e:
        logger.error(f"WebSocket connection error for execution {execution_id}: {e}")
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Internal server error")


@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket_endpoint(
    websocket: WebSocket,
    agent_id: str,
    token: Optional[str] = Query(None),
    user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for agent-level updates and notifications.
    
    Args:
        websocket: WebSocket connection instance
        agent_id: ID of the agent
        token: Authentication token
        user: Authenticated user
    """
    try:
        # Get WebSocket components
        ws_mgr, event_strmr, event_bus, event_store, exec_svc = get_websocket_components()
        
        # Validate agent exists and user has access
        db = next(get_db())
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Agent not found")
            return

        # Check workspace permissions
        await require_workspace_permission(user, agent.workspace_id, "read")

        # Accept WebSocket connection
        connection_id = await ws_mgr.connect_to_agent(websocket, agent_id, user.id)
        logger.info(f"Agent WebSocket connected for agent {agent_id} by user {user.id}")

        try:
            # Send initial agent status
            await send_agent_status(websocket, agent, event_store)

            # Keep connection alive
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle agent-level messages
                    await handle_agent_message(websocket, agent_id, user, message)
                    
                except WebSocketDisconnect:
                    logger.info(f"Agent WebSocket disconnected for agent {agent_id}")
                    break
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client for agent {agent_id}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": "Invalid JSON format"}
                    }))
                except Exception as e:
                    logger.error(f"Error handling agent WebSocket message for agent {agent_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "data": {"message": "Internal server error"}
                    }))

        except WebSocketDisconnect:
            pass
        finally:
            # Clean up connection
            await ws_mgr.disconnect_from_agent(websocket, agent_id, connection_id)
            logger.info(f"Agent WebSocket cleanup completed for agent {agent_id}")

    except HTTPException as e:
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason=str(e.detail))
    except Exception as e:
        logger.error(f"Agent WebSocket connection error for agent {agent_id}: {e}")
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Internal server error")


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection status and statistics.
    """
    ws_mgr, event_strmr, event_bus, event_store, exec_svc = get_websocket_components()
    stats = ws_mgr.get_connection_stats()
    return {
        "status": "active",
        "connections": stats,
        "timestamp": event_store.get_current_timestamp()
    }


@router.post("/ws/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    target_execution_id: Optional[str] = None,
    user: User = Depends(get_current_user_websocket)
):
    """
    Broadcast a message to WebSocket clients.
    
    Args:
        message: Message to broadcast
        target_execution_id: Specific execution to target (optional)
        user: Authenticated user
    """
    ws_mgr, event_strmr, event_bus, event_store, exec_svc = get_websocket_components()
    
    if target_execution_id:
        # Validate user has access to this execution
        execution = await exec_svc.get_execution(target_execution_id)
        if execution:
            await require_workspace_permission(user, execution.agent.workspace_id, "read")
            await ws_mgr.broadcast_to_execution(target_execution_id, message)
        else:
            raise HTTPException(status_code=404, detail="Execution not found")
    else:
        # Broadcast to all connections user has access to
        await ws_mgr.broadcast_to_user(user.id, message)
    
    return {"status": "message sent", "target": target_execution_id or "all_user_connections"}


# Helper functions

async def send_initial_status(websocket: WebSocket, execution: Any):
    """Send initial execution status to newly connected client."""
    try:
        # Get recent events for this execution
        recent_events = await event_store.get_execution_events(
            execution.id, 
            limit=50
        )
        
        # Send execution details
        await websocket.send_text(json.dumps({
            "type": "execution_status",
            "data": {
                "execution_id": execution.id,
                "agent_id": execution.agent_id,
                "status": execution.status,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "metrics": execution.metrics.dict() if execution.metrics else {},
                "input_data": execution.input_data,
                "output_data": execution.output_data,
                "error_message": execution.error_message
            },
            "timestamp": event_store.get_current_timestamp()
        }))
        
        # Send recent events
        for event in recent_events:
            await websocket.send_text(json.dumps({
                "type": "event",
                "data": event.dict(),
                "timestamp": event_store.get_current_timestamp()
            }))
            
    except Exception as e:
        logger.error(f"Error sending initial status: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": "Failed to load initial status"}
        }))


async def send_agent_status(websocket: WebSocket, agent: Any):
    """Send initial agent status to newly connected client."""
    try:
        await websocket.send_text(json.dumps({
            "type": "agent_status",
            "data": {
                "agent_id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "status": agent.status,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "workspace_id": agent.workspace_id
            },
            "timestamp": event_store.get_current_timestamp()
        }))
            
    except Exception as e:
        logger.error(f"Error sending agent status: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": "Failed to load agent status"}
        }))


async def handle_client_message(
    websocket: WebSocket, 
    execution_id: str, 
    user: User, 
    message: Dict[str, Any]
):
    """Handle messages received from WebSocket clients."""
    message_type = message.get("type")
    data = message.get("data", {})
    
    try:
        if message_type == "ping":
            # Respond to ping with pong
            await websocket.send_text(json.dumps({
                "type": "pong",
                "data": {"timestamp": event_store.get_current_timestamp()}
            }))
            
        elif message_type == "subscribe_events":
            # Subscribe to specific event types
            event_types = data.get("event_types", [])
            await event_streamer.subscribe_to_events(execution_id, websocket, event_types)
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "data": {"event_types": event_types}
            }))
            
        elif message_type == "unsubscribe_events":
            # Unsubscribe from specific event types
            event_types = data.get("event_types", [])
            await event_streamer.unsubscribe_from_events(execution_id, websocket, event_types)
            await websocket.send_text(json.dumps({
                "type": "unsubscription_confirmed",
                "data": {"event_types": event_types}
            }))
            
        elif message_type == "cancel_execution":
            # Cancel the execution
            await require_workspace_permission(user, data.get("workspace_id"), "write")
            success = await execution_service.cancel_execution(execution_id)
            await websocket.send_text(json.dumps({
                "type": "cancel_response",
                "data": {"success": success}
            }))
            
        elif message_type == "pause_execution":
            # Pause the execution
            await require_workspace_permission(user, data.get("workspace_id"), "write")
            success = await execution_service.pause_execution(execution_id)
            await websocket.send_text(json.dumps({
                "type": "pause_response",
                "data": {"success": success}
            }))
            
        elif message_type == "resume_execution":
            # Resume the execution
            await require_workspace_permission(user, data.get("workspace_id"), "write")
            success = await execution_service.resume_execution(execution_id)
            await websocket.send_text(json.dumps({
                "type": "resume_response",
                "data": {"success": success}
            }))
            
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"}
            }))
            
    except Exception as e:
        logger.error(f"Error handling client message {message_type}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": "Failed to process message"}
        }))


async def handle_agent_message(
    websocket: WebSocket,
    agent_id: str,
    user: User,
    message: Dict[str, Any]
):
    """Handle agent-level messages from WebSocket clients."""
    message_type = message.get("type")
    data = message.get("data", {})
    
    try:
        if message_type == "ping":
            await websocket.send_text(json.dumps({
                "type": "pong",
                "data": {"timestamp": event_store.get_current_timestamp()}
            }))
            
        elif message_type == "get_executions":
            # Get recent executions for this agent
            executions = await execution_service.get_agent_executions(
                agent_id, 
                limit=data.get("limit", 10)
            )
            await websocket.send_text(json.dumps({
                "type": "executions_list",
                "data": {
                    "executions": [exec.dict() for exec in executions],
                    "agent_id": agent_id
                }
            }))
            
        else:
            logger.warning(f"Unknown agent message type: {message_type}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"}
            }))
            
    except Exception as e:
        logger.error(f"Error handling agent message {message_type}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": "Failed to process message"}
        }))


# Initialize event streamer on startup
async def initialize_websocket_endpoints():
    """Initialize WebSocket endpoints and event streaming."""
    await event_streamer.initialize()
    logger.info("WebSocket endpoints initialized")

# Export for initialization
__all__ = ["router", "initialize_websocket_endpoints"]