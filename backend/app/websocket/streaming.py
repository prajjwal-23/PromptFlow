"""
Event Streaming for PromptFlow WebSocket Manager.

This module provides real-time event streaming capabilities including:
- Event filtering and routing
- Subscription management
- Event transformation and formatting
- Backpressure handling
- Event replay and caching
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import weakref

from app.events.bus import EventBus
from app.domain.execution.models import ExecutionEvent
from app.core.logging import get_logger
from .manager import WebSocketManager, MessageType, WebSocketMessage


class StreamEventType(Enum):
    """Stream event types for WebSocket communication."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    WORKSPACE_DELETED = "workspace_deleted"
    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
    SYSTEM_STATUS = "system_status"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class StreamFilter:
    """Event stream filter criteria."""
    event_types: Set[StreamEventType] = field(default_factory=set)
    user_ids: Set[str] = field(default_factory=set)
    workspace_ids: Set[str] = field(default_factory=set)
    agent_ids: Set[str] = field(default_factory=set)
    execution_ids: Set[str] = field(default_factory=set)
    node_ids: Set[str] = field(default_factory=set)
    
    def matches(self, event_data: Dict[str, Any]) -> bool:
        """Check if event matches filter criteria."""
        # Check event type
        if self.event_types:
            event_type = event_data.get("event_type")
            if event_type not in [et.value for et in self.event_types]:
                return False
        
        # Check user IDs
        if self.user_ids:
            user_id = event_data.get("user_id")
            if user_id not in self.user_ids:
                return False
        
        # Check workspace IDs
        if self.workspace_ids:
            workspace_id = event_data.get("workspace_id")
            if workspace_id not in self.workspace_ids:
                return False
        
        # Check agent IDs
        if self.agent_ids:
            agent_id = event_data.get("agent_id")
            if agent_id not in self.agent_ids:
                return False
        
        # Check execution IDs
        if self.execution_ids:
            execution_id = event_data.get("execution_id")
            if execution_id not in self.execution_ids:
                return False
        
        # Check node IDs
        if self.node_ids:
            node_id = event_data.get("node_id")
            if node_id not in self.node_ids:
                return False
        
        return True


@dataclass
class StreamSubscription:
    """Event stream subscription."""
    subscription_id: str
    connection_id: str
    filter: StreamFilter
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_event_at: Optional[datetime] = None
    event_count: int = 0
    
    def should_receive_event(self, event_data: Dict[str, Any]) -> bool:
        """Check if subscription should receive event."""
        if self.filter.matches(event_data):
            self.last_event_at = datetime.now(timezone.utc)
            self.event_count += 1
            return True
        return False


@dataclass
class EventCache:
    """Event cache for replay functionality."""
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1 hour
    
    def __post_init__(self):
        self._events: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def add_event(self, event_data: Dict[str, Any]) -> None:
        """Add event to cache."""
        async with self._lock:
            # Add timestamp if not present
            if "timestamp" not in event_data:
                event_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Add to cache
            self._events.append(event_data)
            
            # Remove old events if cache is full
            if len(self._events) > self.max_size:
                self._events.pop(0)
            
            # Remove expired events
            await self._remove_expired_events()
    
    async def get_events(
        self,
        filter_criteria: Optional[StreamFilter] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get events from cache."""
        async with self._lock:
            events = self._events.copy()
            
            # Apply time filter
            if since:
                events = [
                    event for event in events
                    if datetime.fromisoformat(event["timestamp"]) >= since
                ]
            
            # Apply custom filter
            if filter_criteria:
                events = [
                    event for event in events
                    if filter_criteria.matches(event)
                ]
            
            return events
    
    async def _remove_expired_events(self) -> None:
        """Remove expired events from cache."""
        if not self._events:
            return
        
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time.timestamp() - self.ttl_seconds
        
        # Remove expired events
        self._events = [
            event for event in self._events
            if datetime.fromisoformat(event["timestamp"]).timestamp() > cutoff_time
        ]
    
    async def clear(self) -> None:
        """Clear all events from cache."""
        async with self._lock:
            self._events.clear()


class EventStreamer:
    """Enterprise-grade event streaming for WebSocket connections."""
    
    def __init__(
        self,
        websocket_manager: WebSocketManager,
        event_bus: EventBus,
        cache_size: int = 1000,
        cache_ttl: int = 3600
    ):
        """
        Initialize event streamer.
        
        Args:
            websocket_manager: WebSocket manager instance
            event_bus: Event bus for subscribing to events
            cache_size: Maximum cache size
            cache_ttl: Cache TTL in seconds
        """
        self._websocket_manager = websocket_manager
        self._event_bus = event_bus
        self._cache = EventCache(max_size=cache_size, ttl_seconds=cache_ttl)
        self._subscriptions: Dict[str, StreamSubscription] = {}
        self._lock = asyncio.Lock()
        self._logger = get_logger(f"{__name__}.EventStreamer")
        
        # Event transformers
        self._transformers: Dict[str, Callable] = {}
        
        # Start event processing
        self._start_event_processing()
    
    def _start_event_processing(self) -> None:
        """Start processing events from event bus."""
        # Subscribe to all events using subscribe_all
        import asyncio
        asyncio.create_task(self._event_bus.subscribe_all(self._handle_domain_event))
        
        self._logger.info("Event streamer started and subscribed to event bus")
    
    async def _handle_domain_event(self, event: ExecutionEvent) -> None:
        """
        Handle domain event and stream to WebSocket clients.
        
        Args:
            event: Domain event
        """
        try:
            # Transform domain event to stream event
            stream_event = await self._transform_event(event)
            
            # Add to cache
            await self._cache.add_event(stream_event)
            
            # Find matching subscriptions
            matching_subscriptions = []
            async with self._lock:
                for subscription in self._subscriptions.values():
                    if subscription.should_receive_event(stream_event):
                        matching_subscriptions.append(subscription)
            
            # Stream to matching connections
            for subscription in matching_subscriptions:
                await self._stream_to_connection(
                    subscription.connection_id,
                    stream_event
                )
            
        except Exception as e:
            self._logger.error(f"Error handling domain event: {e}")
    
    async def _transform_event(self, event: ExecutionEvent) -> Dict[str, Any]:
        """
        Transform domain event to stream event format.
        
        Args:
            event: Domain event
            
        Returns:
            Stream event data
        """
        # Base event data
        stream_event = {
            "event_id": event.event_id,
            "event_type": self._map_event_type(event.event_type.value),
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        }
        
        # Add common fields from event data
        event_data = event.data or {}
        stream_event.update({
            "user_id": event_data.get("user_id"),
            "workspace_id": event_data.get("workspace_id"),
            "agent_id": event_data.get("agent_id"),
            "execution_id": event_data.get("execution_id"),
            "node_id": event_data.get("node_id")
        })
        
        # Apply custom transformer if available
        transformer = self._transformers.get(event.event_type.value)
        if transformer:
            try:
                stream_event = transformer(stream_event)
            except Exception as e:
                self._logger.error(f"Error in event transformer: {e}")
        
        return stream_event
    
    def _map_event_type(self, domain_event_type: str) -> str:
        """
        Map domain event type to stream event type.
        
        Args:
            domain_event_type: Domain event type
            
        Returns:
            Stream event type
        """
        mapping = {
            "execution.started": StreamEventType.EXECUTION_STARTED.value,
            "execution.completed": StreamEventType.EXECUTION_COMPLETED.value,
            "execution.failed": StreamEventType.EXECUTION_FAILED.value,
            "node.started": StreamEventType.NODE_STARTED.value,
            "node.completed": StreamEventType.NODE_COMPLETED.value,
            "node.failed": StreamEventType.NODE_FAILED.value,
            "agent.created": StreamEventType.AGENT_CREATED.value,
            "agent.updated": StreamEventType.AGENT_UPDATED.value,
            "agent.deleted": StreamEventType.AGENT_DELETED.value,
            "workspace.created": StreamEventType.WORKSPACE_CREATED.value,
            "workspace.updated": StreamEventType.WORKSPACE_UPDATED.value,
            "workspace.deleted": StreamEventType.WORKSPACE_DELETED.value,
            "user.connected": StreamEventType.USER_CONNECTED.value,
            "user.disconnected": StreamEventType.USER_DISCONNECTED.value,
        }
        
        return mapping.get(domain_event_type, domain_event_type)
    
    async def _stream_to_connection(
        self,
        connection_id: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Stream event to specific WebSocket connection.
        
        Args:
            connection_id: Target connection ID
            event_data: Event data to stream
        """
        try:
            message = WebSocketMessage(
                type=MessageType.EVENT,
                data=event_data
            )
            
            await self._websocket_manager.send_message(
                connection_id,
                MessageType.EVENT,
                event_data
            )
            
        except Exception as e:
            self._logger.error(f"Error streaming event to {connection_id}: {e}")
    
    async def subscribe_to_events(
        self,
        connection_id: str,
        filter_criteria: Optional[StreamFilter] = None,
        replay_events: bool = False,
        replay_since: Optional[datetime] = None
    ) -> str:
        """
        Subscribe connection to event stream.
        
        Args:
            connection_id: Connection ID
            filter_criteria: Event filter criteria
            replay_events: Whether to replay historical events
            replay_since: Replay events since this time
            
        Returns:
            Subscription ID
        """
        subscription_id = f"sub_{connection_id}_{datetime.now(timezone.utc).timestamp()}"
        
        subscription = StreamSubscription(
            subscription_id=subscription_id,
            connection_id=connection_id,
            filter=filter_criteria or StreamFilter()
        )
        
        async with self._lock:
            self._subscriptions[subscription_id] = subscription
        
        # Replay events if requested
        if replay_events:
            await self._replay_events(connection_id, subscription.filter, replay_since)
        
        self._logger.info(
            f"Created subscription {subscription_id} for connection {connection_id}"
        )
        
        return subscription_id
    
    async def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """
        Unsubscribe from event stream.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if unsubscribed successfully
        """
        async with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                self._logger.info(f"Removed subscription {subscription_id}")
                return True
        
        return False
    
    async def unsubscribe_connection(self, connection_id: str) -> int:
        """
        Unsubscribe all subscriptions for a connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Number of subscriptions removed
        """
        removed_count = 0
        
        async with self._lock:
            subscriptions_to_remove = [
                sub_id for sub_id, sub in self._subscriptions.items()
                if sub.connection_id == connection_id
            ]
            
            for sub_id in subscriptions_to_remove:
                del self._subscriptions[sub_id]
                removed_count += 1
        
        if removed_count > 0:
            self._logger.info(
                f"Removed {removed_count} subscriptions for connection {connection_id}"
            )
        
        return removed_count
    
    async def _replay_events(
        self,
        connection_id: str,
        filter_criteria: StreamFilter,
        since: Optional[datetime]
    ) -> None:
        """
        Replay historical events to connection.
        
        Args:
            connection_id: Target connection ID
            filter_criteria: Event filter criteria
            since: Replay events since this time
        """
        try:
            events = await self._cache.get_events(filter_criteria, since)
            
            for event in events:
                await self._stream_to_connection(connection_id, event)
            
            self._logger.info(
                f"Replayed {len(events)} events to connection {connection_id}"
            )
            
        except Exception as e:
            self._logger.error(f"Error replaying events: {e}")
    
    def register_transformer(
        self,
        event_type: str,
        transformer: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Register custom event transformer.
        
        Args:
            event_type: Event type to transform
            transformer: Transformer function
        """
        self._transformers[event_type] = transformer
        self._logger.info(f"Registered transformer for event type: {event_type}")
    
    def unregister_transformer(self, event_type: str) -> None:
        """
        Unregister event transformer.
        
        Args:
            event_type: Event type to unregister
        """
        if event_type in self._transformers:
            del self._transformers[event_type]
            self._logger.info(f"Unregistered transformer for event type: {event_type}")
    
    async def get_subscription_info(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription information.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription information
        """
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return None
            
            subscription = self._subscriptions[subscription_id]
            return {
                "subscription_id": subscription.subscription_id,
                "connection_id": subscription.connection_id,
                "created_at": subscription.created_at.isoformat(),
                "last_event_at": subscription.last_event_at.isoformat() if subscription.last_event_at else None,
                "event_count": subscription.event_count,
                "filter": {
                    "event_types": [et.value for et in subscription.filter.event_types],
                    "user_ids": list(subscription.filter.user_ids),
                    "workspace_ids": list(subscription.filter.workspace_ids),
                    "agent_ids": list(subscription.filter.agent_ids),
                    "execution_ids": list(subscription.filter.execution_ids),
                    "node_ids": list(subscription.filter.node_ids)
                }
            }
    
    async def get_all_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all subscriptions."""
        subscriptions_info = []
        
        async with self._lock:
            for subscription in self._subscriptions.values():
                subscriptions_info.append({
                    "subscription_id": subscription.subscription_id,
                    "connection_id": subscription.connection_id,
                    "created_at": subscription.created_at.isoformat(),
                    "last_event_at": subscription.last_event_at.isoformat() if subscription.last_event_at else None,
                    "event_count": subscription.event_count
                })
        
        return subscriptions_info
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get event cache statistics."""
        events = await self._cache.get_events()
        
        return {
            "total_events": len(events),
            "max_size": self._cache.max_size,
            "ttl_seconds": self._cache.ttl_seconds,
            "oldest_event": events[0]["timestamp"] if events else None,
            "newest_event": events[-1]["timestamp"] if events else None
        }
    
    async def clear_cache(self) -> None:
        """Clear event cache."""
        await self._cache.clear()
        self._logger.info("Event cache cleared")
    
    async def shutdown(self) -> None:
        """Shutdown event streamer."""
        try:
            # Clear all subscriptions
            async with self._lock:
                self._subscriptions.clear()
            
            # Clear cache
            await self._cache.clear()
            
            # Note: unsubscribe_all is not available, we'll handle this differently
            # The event bus will be shutdown anyway
            
            self._logger.info("Event streamer shutdown complete")
            
        except Exception as e:
            self._logger.error(f"Error during shutdown: {e}")


# Global event streamer instance
event_streamer: Optional[EventStreamer] = None


def initialize_event_streamer(
    websocket_manager: WebSocketManager,
    event_bus: EventBus
) -> EventStreamer:
    """
    Initialize global event streamer.
    
    Args:
        websocket_manager: WebSocket manager instance
        event_bus: Event bus instance
        
    Returns:
        Event streamer instance
    """
    global event_streamer
    event_streamer = EventStreamer(websocket_manager, event_bus)
    return event_streamer


def get_event_streamer() -> Optional[EventStreamer]:
    """Get global event streamer instance."""
    return event_streamer