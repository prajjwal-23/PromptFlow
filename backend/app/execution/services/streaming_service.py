"""
Streaming Service Implementation

This module provides the concrete implementation of the StreamingService
interface for real-time event streaming with WebSocket integration.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Callable, AsyncIterator
from datetime import datetime, timezone
import asyncio
import logging
from uuid import uuid4

from app.domain.execution.models import ExecutionEvent, EventType
from app.domain.execution.services import StreamingService
from app.websocket.manager import get_websocket_manager
from app.websocket.streaming import get_event_streamer
from app.events.bus import get_event_bus
from app.core.logging import get_logger

logger = get_logger(__name__)


class StreamingServiceImpl(StreamingService):
    """Concrete implementation of StreamingService."""
    
    def __init__(self):
        """Initialize streaming service."""
        self.logger = logger
        self.websocket_manager = get_websocket_manager()
        self.event_streamer = get_event_streamer()
        self.event_bus = get_event_bus()
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._active_streams: Dict[str, asyncio.Task] = {}
    
    async def start_stream(
        self,
        execution_id: str,
        client_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Start streaming events for an execution."""
        try:
            self.logger.info(f"Starting stream for execution {execution_id} to client {client_id}")
            
            # Create subscription for this execution
            subscription_id = str(uuid4())
            
            # Subscribe to execution events
            async for event in self._stream_execution_events(execution_id, client_id, subscription_id):
                yield event
            
        except Exception as e:
            self.logger.error(f"Error in stream for execution {execution_id}: {e}")
            raise
        finally:
            # Clean up subscription
            await self._cleanup_stream(execution_id, client_id)
    
    async def send_event(
        self,
        execution_id: str,
        event: ExecutionEvent
    ) -> None:
        """Send event to stream."""
        try:
            # Convert event to dictionary
            event_data = {
                "type": "execution_event",
                "execution_id": execution_id,
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "metadata": event.metadata,
                "node_id": event.node_id
            }
            
            # Send via WebSocket manager
            await self.websocket_manager.send_to_execution(execution_id, event_data)
            
            # Send via event streamer
            await self.event_streamer.publish_event(execution_id, event_data)
            
            # Emit to event bus
            await self.event_bus.emit(event)
            
            self.logger.debug(f"Sent event {event.event_type} for execution {execution_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending event for execution {execution_id}: {e}")
            raise
    
    async def subscribe_to_execution(
        self,
        execution_id: str,
        callback: Callable[[ExecutionEvent], None]
    ) -> str:
        """Subscribe to execution events. Returns subscription ID."""
        try:
            subscription_id = str(uuid4())
            
            # Add subscription to local registry
            if execution_id not in self._subscriptions:
                self._subscriptions[execution_id] = []
            
            self._subscriptions[execution_id].append((subscription_id, callback))
            
            # Subscribe to event bus
            async def event_handler(event: ExecutionEvent):
                if event.execution_id == execution_id:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        self.logger.error(f"Error in subscription callback: {e}")
            
            await self.event_bus.subscribe(EventType.EXECUTION_STARTED, event_handler)
            await self.event_bus.subscribe(EventType.EXECUTION_COMPLETED, event_handler)
            await self.event_bus.subscribe(EventType.EXECUTION_FAILED, event_handler)
            await self.event_bus.subscribe(EventType.NODE_STARTED, event_handler)
            await self.event_bus.subscribe(EventType.NODE_COMPLETED, event_handler)
            await self.event_bus.subscribe(EventType.NODE_FAILED, event_handler)
            
            self.logger.info(f"Added subscription {subscription_id} for execution {execution_id}")
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Error subscribing to execution {execution_id}: {e}")
            raise
    
    async def unsubscribe_from_execution(
        self,
        execution_id: str,
        subscription_id: str
    ) -> bool:
        """Unsubscribe from execution events."""
        try:
            if execution_id in self._subscriptions:
                # Remove subscription from local registry
                original_count = len(self._subscriptions[execution_id])
                self._subscriptions[execution_id] = [
                    (sub_id, callback) for sub_id, callback in self._subscriptions[execution_id]
                    if sub_id != subscription_id
                ]
                
                if len(self._subscriptions[execution_id]) < original_count:
                    self.logger.info(f"Removed subscription {subscription_id} for execution {execution_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from execution {execution_id}: {e}")
            raise
    
    async def get_active_streams(self) -> List[str]:
        """Get list of active stream IDs."""
        try:
            # Get active connections from WebSocket manager
            active_connections = await self.websocket_manager.get_active_connections()
            
            # Extract execution IDs from connections
            execution_ids = []
            for connection in active_connections:
                if hasattr(connection, 'execution_id') and connection.execution_id:
                    execution_ids.append(connection.execution_id)
            
            return list(set(execution_ids))
            
        except Exception as e:
            self.logger.error(f"Error getting active streams: {e}")
            return []
    
    async def _stream_execution_events(
        self,
        execution_id: str,
        client_id: str,
        subscription_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream execution events to client."""
        try:
            # Create event queue for this stream
            event_queue = asyncio.Queue()
            
            # Subscribe to events
            async def event_handler(event: ExecutionEvent):
                if event.execution_id == execution_id:
                    event_data = {
                        "type": "execution_event",
                        "execution_id": execution_id,
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "data": event.data,
                        "metadata": event.metadata,
                        "node_id": event.node_id
                    }
                    await event_queue.put(event_data)
            
            # Subscribe to event bus
            event_types = [
                EventType.EXECUTION_STARTED,
                EventType.EXECUTION_COMPLETED,
                EventType.EXECUTION_FAILED,
                EventType.EXECUTION_CANCELLED,
                EventType.NODE_STARTED,
                EventType.NODE_COMPLETED,
                EventType.NODE_FAILED,
                EventType.NODE_SKIPPED,
                EventType.TOKEN_STREAM,
                EventType.ERROR_OCCURRED
            ]
            
            subscriptions = []
            for event_type in event_types:
                subscription = await self.event_bus.subscribe(event_type, event_handler)
                subscriptions.append(subscription)
            
            try:
                # Send initial status
                initial_event = {
                    "type": "stream_started",
                    "execution_id": execution_id,
                    "client_id": client_id,
                    "subscription_id": subscription_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                yield initial_event
                
                # Stream events
                while True:
                    try:
                        # Wait for event with timeout
                        event_data = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                        yield event_data
                        
                    except asyncio.TimeoutError:
                        # Send heartbeat
                        heartbeat = {
                            "type": "heartbeat",
                            "execution_id": execution_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        yield heartbeat
                        
            except Exception as e:
                self.logger.error(f"Error in event stream: {e}")
            finally:
                # Clean up subscriptions
                for subscription in subscriptions:
                    await self.event_bus.unsubscribe(subscription)
                
        except Exception as e:
            self.logger.error(f"Error in stream execution events: {e}")
            raise
    
    async def _cleanup_stream(self, execution_id: str, client_id: str) -> None:
        """Clean up stream resources."""
        try:
            # Remove from active streams
            stream_key = f"{execution_id}:{client_id}"
            if stream_key in self._active_streams:
                task = self._active_streams[stream_key]
                if not task.done():
                    task.cancel()
                del self._active_streams[stream_key]
            
            # Send stream ended event
            end_event = {
                "type": "stream_ended",
                "execution_id": execution_id,
                "client_id": client_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.websocket_manager.send_to_execution(execution_id, end_event)
            
            self.logger.info(f"Cleaned up stream for execution {execution_id}, client {client_id}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up stream: {e}")
    
    async def broadcast_system_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast system event to all connected clients."""
        try:
            system_event = {
                "type": "system_event",
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.websocket_manager.broadcast(system_event)
            self.logger.info(f"Broadcasted system event: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting system event: {e}")
    
    async def get_stream_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        try:
            active_streams = await self.get_active_streams()
            active_connections = await self.websocket_manager.get_active_connections()
            
            return {
                "active_streams": len(active_streams),
                "active_connections": len(active_connections),
                "execution_ids": active_streams,
                "subscriptions": {
                    execution_id: len(subscriptions)
                    for execution_id, subscriptions in self._subscriptions.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stream statistics: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on streaming service."""
        try:
            # Check WebSocket manager
            ws_health = await self.websocket_manager.health_check()
            
            # Check event streamer
            streamer_health = await self.event_streamer.health_check()
            
            # Check event bus
            event_bus_health = await self.event_bus.health_check()
            
            # Get statistics
            stats = await self.get_stream_statistics()
            
            overall_status = "healthy"
            if any([
                ws_health.get("status") != "healthy",
                streamer_health.get("status") != "healthy",
                event_bus_health.get("status") != "healthy"
            ]):
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "websocket_manager": ws_health,
                "event_streamer": streamer_health,
                "event_bus": event_bus_health,
                "statistics": stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


# Factory function
def create_streaming_service() -> StreamingService:
    """Create streaming service instance."""
    return StreamingServiceImpl()