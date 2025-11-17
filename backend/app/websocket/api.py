"""
WebSocket API endpoints for PromptFlow.

This module provides WebSocket API endpoints including:
- Connection management
- Event streaming
- Subscription management
- Authentication and authorization
- Real-time communication
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.auth import get_optional_current_user
from app.core.logging import get_logger
from app.models.user import User
from .manager import websocket_manager, WebSocketConfig, MessageType
from .streaming import (
    get_event_streamer,
    StreamFilter,
    StreamEventType,
    initialize_event_streamer
)
from app.events.bus import get_event_bus


router = APIRouter(prefix="/ws", tags=["websocket"])
logger = get_logger(f"{__name__}.WebSocketAPI")


# WebSocket API Models
class WebSocketConnectRequest(BaseModel):
    """WebSocket connection request."""
    workspace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WebSocketSubscribeRequest(BaseModel):
    """WebSocket subscription request."""
    event_types: Optional[List[str]] = Field(default_factory=list)
    user_ids: Optional[List[str]] = Field(default_factory=list)
    workspace_ids: Optional[List[str]] = Field(default_factory=list)
    agent_ids: Optional[List[str]] = Field(default_factory=list)
    execution_ids: Optional[List[str]] = Field(default_factory=list)
    node_ids: Optional[List[str]] = Field(default_factory=list)
    replay_events: bool = False
    replay_since: Optional[datetime] = None


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    subscription_id: str
    status: str
    message: str


# WebSocket Connection Endpoint
@router.websocket("/connect")
async def websocket_connect(
    websocket: WebSocket,
    workspace_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    """
    WebSocket connection endpoint for real-time communication.
    
    Query Parameters:
    - workspace_id: Optional workspace ID for scoping
    - user_id: Optional user ID (for testing)
    - token: Authentication token
    
    Supported Message Types:
    - subscribe: Subscribe to events
    - unsubscribe: Unsubscribe from events
    - ping: Ping message
    - get_info: Get connection information
    """
    connection_id = None
    
    try:
        # Authenticate user (optional for now)
        current_user = None
        if token:
            # TODO: Implement token validation
            pass
        
        # Extract user ID from token or query parameter
        effective_user_id = user_id or (current_user.id if current_user else None)
        
        # Connect WebSocket
        connection_id = await websocket_manager.connect(
            websocket=websocket,
            user_id=effective_user_id,
            workspace_id=workspace_id,
            metadata={"authenticated": current_user is not None}
        )
        
        logger.info(f"WebSocket connected: {connection_id} (user: {effective_user_id}, workspace: {workspace_id})")
        
        # Initialize event streamer if not already done
        event_streamer = get_event_streamer()
        if not event_streamer:
            event_bus = get_event_bus()
            initialize_event_streamer(websocket_manager, event_bus)
            event_streamer = get_event_streamer()
        
        # Handle WebSocket messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process message
                await _handle_websocket_message(
                    connection_id,
                    message_data,
                    websocket,
                    effective_user_id,
                    workspace_id
                )
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Send error message
                await websocket_manager.send_message(
                    connection_id,
                    MessageType.ERROR,
                    {"error": "Failed to process message", "details": str(e)}
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during connection: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if connection_id:
            await websocket_manager.send_message(
                connection_id,
                MessageType.ERROR,
                {"error": "Connection error", "details": str(e)}
            )
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id, "Connection closed")
            
            # Clean up event subscriptions
            event_streamer = get_event_streamer()
            if event_streamer:
                await event_streamer.unsubscribe_connection(connection_id)


async def _handle_websocket_message(
    connection_id: str,
    message_data: Dict[str, Any],
    websocket: WebSocket,
    user_id: Optional[str],
    workspace_id: Optional[str]
):
    """
    Handle incoming WebSocket message.
    
    Args:
        connection_id: Connection ID
        message_data: Message data
        websocket: WebSocket connection
        user_id: User ID
        workspace_id: Workspace ID
    """
    message_type = message_data.get("type", "").lower()
    data = message_data.get("data", {})
    
    try:
        if message_type == "subscribe":
            await _handle_subscribe_message(connection_id, data, user_id, workspace_id)
        
        elif message_type == "unsubscribe":
            await _handle_unsubscribe_message(connection_id, data)
        
        elif message_type == "ping":
            await _handle_ping_message(connection_id)
        
        elif message_type == "get_info":
            await _handle_get_info_message(connection_id)
        
        elif message_type == "get_metrics":
            await _handle_get_metrics_message(connection_id)
        
        elif message_type == "get_subscriptions":
            await _handle_get_subscriptions_message(connection_id)
        
        else:
            await websocket_manager.send_message(
                connection_id,
                MessageType.ERROR,
                {"error": f"Unknown message type: {message_type}"}
            )
    
    except Exception as e:
        logger.error(f"Error handling {message_type} message: {e}")
        await websocket_manager.send_message(
            connection_id,
            MessageType.ERROR,
            {"error": f"Failed to handle {message_type}", "details": str(e)}
        )


async def _handle_subscribe_message(
    connection_id: str,
    data: Dict[str, Any],
    user_id: Optional[str],
    workspace_id: Optional[str]
):
    """
    Handle subscription message.
    
    Args:
        connection_id: Connection ID
        data: Subscription data
        user_id: User ID
        workspace_id: Workspace ID
    """
    event_streamer = get_event_streamer()
    if not event_streamer:
        await websocket_manager.send_message(
            connection_id,
            MessageType.ERROR,
            {"error": "Event streamer not available"}
        )
        return
    
    # Create filter
    filter_criteria = StreamFilter()
    
    # Parse event types
    event_types = data.get("event_types", [])
    for event_type in event_types:
        try:
            filter_criteria.event_types.add(StreamEventType(event_type))
        except ValueError:
            # Invalid event type, skip
            pass
    
    # Parse other filter criteria
    filter_criteria.user_ids.update(data.get("user_ids", []))
    filter_criteria.workspace_ids.update(data.get("workspace_ids", []))
    filter_criteria.agent_ids.update(data.get("agent_ids", []))
    filter_criteria.execution_ids.update(data.get("execution_ids", []))
    filter_criteria.node_ids.update(data.get("node_ids", []))
    
    # Add current user and workspace if not specified
    if user_id and not filter_criteria.user_ids:
        filter_criteria.user_ids.add(user_id)
    
    if workspace_id and not filter_criteria.workspace_ids:
        filter_criteria.workspace_ids.add(workspace_id)
    
    # Parse replay options
    replay_events = data.get("replay_events", False)
    replay_since = None
    if data.get("replay_since"):
        try:
            replay_since = datetime.fromisoformat(data["replay_since"])
        except ValueError:
            pass
    
    # Create subscription
    subscription_id = await event_streamer.subscribe_to_events(
        connection_id=connection_id,
        filter_criteria=filter_criteria,
        replay_events=replay_events,
        replay_since=replay_since
    )
    
    # Send confirmation
    await websocket_manager.send_message(
        connection_id,
        MessageType.SUBSCRIBE,
        {
            "subscription_id": subscription_id,
            "status": "subscribed",
            "filter": {
                "event_types": [et.value for et in filter_criteria.event_types],
                "user_ids": list(filter_criteria.user_ids),
                "workspace_ids": list(filter_criteria.workspace_ids),
                "agent_ids": list(filter_criteria.agent_ids),
                "execution_ids": list(filter_criteria.execution_ids),
                "node_ids": list(filter_criteria.node_ids)
            },
            "replay_events": replay_events,
            "replay_since": replay_since.isoformat() if replay_since else None
        }
    )


async def _handle_unsubscribe_message(connection_id: str, data: Dict[str, Any]):
    """
    Handle unsubscription message.
    
    Args:
        connection_id: Connection ID
        data: Unsubscription data
    """
    event_streamer = get_event_streamer()
    if not event_streamer:
        await websocket_manager.send_message(
            connection_id,
            MessageType.ERROR,
            {"error": "Event streamer not available"}
        )
        return
    
    subscription_id = data.get("subscription_id")
    if not subscription_id:
        # Unsubscribe all subscriptions for this connection
        removed_count = await event_streamer.unsubscribe_connection(connection_id)
        
        await websocket_manager.send_message(
            connection_id,
            MessageType.UNSUBSCRIBE,
            {
                "status": "unsubscribed_all",
                "removed_count": removed_count
            }
        )
    else:
        # Unsubscribe specific subscription
        success = await event_streamer.unsubscribe_from_events(subscription_id)
        
        await websocket_manager.send_message(
            connection_id,
            MessageType.UNSUBSCRIBE,
            {
                "subscription_id": subscription_id,
                "status": "unsubscribed" if success else "not_found"
            }
        )


async def _handle_ping_message(connection_id: str):
    """
    Handle ping message.
    
    Args:
        connection_id: Connection ID
    """
    await websocket_manager.send_message(
        connection_id,
        MessageType.HEARTBEAT,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connection_id": connection_id
        }
    )


async def _handle_get_info_message(connection_id: str):
    """
    Handle get info message.
    
    Args:
        connection_id: Connection ID
    """
    connection_info = await websocket_manager.get_connection_info(connection_id)
    
    await websocket_manager.send_message(
        connection_id,
        MessageType.EVENT,
        {
            "type": "connection_info",
            "data": connection_info or {"error": "Connection not found"}
        }
    )


async def _handle_get_metrics_message(connection_id: str):
    """
    Handle get metrics message.
    
    Args:
        connection_id: Connection ID
    """
    metrics = websocket_manager.get_metrics()
    
    await websocket_manager.send_message(
        connection_id,
        MessageType.EVENT,
        {
            "type": "metrics",
            "data": metrics.to_dict()
        }
    )


async def _handle_get_subscriptions_message(connection_id: str):
    """
    Handle get subscriptions message.
    
    Args:
        connection_id: Connection ID
    """
    event_streamer = get_event_streamer()
    if not event_streamer:
        await websocket_manager.send_message(
            connection_id,
            MessageType.ERROR,
            {"error": "Event streamer not available"}
        )
        return
    
    subscriptions = await event_streamer.get_all_subscriptions()
    connection_subscriptions = [
        sub for sub in subscriptions
        if sub["connection_id"] == connection_id
    ]
    
    await websocket_manager.send_message(
        connection_id,
        MessageType.EVENT,
        {
            "type": "subscriptions",
            "data": connection_subscriptions
        }
    )


# REST API Endpoints for WebSocket Management
@router.get("/connections")
async def get_connections(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get all WebSocket connections (admin only)."""
    # TODO: Add admin authorization
    connections = await websocket_manager.get_all_connections()
    return JSONResponse(content={"connections": connections})


@router.get("/connections/{connection_id}")
async def get_connection(
    connection_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get specific WebSocket connection information."""
    connection_info = await websocket_manager.get_connection_info(connection_id)
    
    if not connection_info:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return JSONResponse(content=connection_info)


@router.get("/metrics")
async def get_websocket_metrics(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get WebSocket metrics."""
    metrics = websocket_manager.get_metrics()
    return JSONResponse(content=metrics.to_dict())


@router.get("/subscriptions")
async def get_subscriptions(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get all event subscriptions."""
    event_streamer = get_event_streamer()
    if not event_streamer:
        return JSONResponse(content={"subscriptions": []})
    
    subscriptions = await event_streamer.get_all_subscriptions()
    return JSONResponse(content={"subscriptions": subscriptions})


@router.get("/subscriptions/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get specific subscription information."""
    event_streamer = get_event_streamer()
    if not event_streamer:
        raise HTTPException(status_code=404, detail="Event streamer not available")
    
    subscription_info = await event_streamer.get_subscription_info(subscription_id)
    
    if not subscription_info:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return JSONResponse(content=subscription_info)


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get event cache statistics."""
    event_streamer = get_event_streamer()
    if not event_streamer:
        return JSONResponse(content={"error": "Event streamer not available"})
    
    stats = await event_streamer.get_cache_stats()
    return JSONResponse(content=stats)


@router.delete("/cache")
async def clear_cache(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Clear event cache (admin only)."""
    # TODO: Add admin authorization
    event_streamer = get_event_streamer()
    if not event_streamer:
        return JSONResponse(content={"error": "Event streamer not available"})
    
    await event_streamer.clear_cache()
    return JSONResponse(content={"message": "Cache cleared"})


@router.get("/dead-letter")
async def get_dead_letter_messages(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get dead letter messages (admin only)."""
    # TODO: Add admin authorization
    messages = await websocket_manager.get_dead_letter_messages()
    return JSONResponse(content={"messages": messages})


@router.post("/broadcast")
async def broadcast_message(
    message: WebSocketMessage,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Broadcast message to all connections (admin only)."""
    # TODO: Add admin authorization
    
    sent_count = await websocket_manager.broadcast_to_all(
        MessageType(message.type.upper()),
        message.data
    )
    
    return JSONResponse(content={
        "message": "Broadcast sent",
        "sent_count": sent_count
    })


@router.post("/broadcast/workspace/{workspace_id}")
async def broadcast_to_workspace(
    workspace_id: str,
    message: WebSocketMessage,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Broadcast message to workspace connections."""
    sent_count = await websocket_manager.broadcast_to_workspace(
        workspace_id,
        MessageType(message.type.upper()),
        message.data
    )
    
    return JSONResponse(content={
        "message": f"Broadcast sent to workspace {workspace_id}",
        "sent_count": sent_count
    })


@router.post("/broadcast/user/{user_id}")
async def broadcast_to_user(
    user_id: str,
    message: WebSocketMessage,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Broadcast message to user connections."""
    sent_count = await websocket_manager.broadcast_to_user(
        user_id,
        MessageType(message.type.upper()),
        message.data
    )
    
    return JSONResponse(content={
        "message": f"Broadcast sent to user {user_id}",
        "sent_count": sent_count
    })