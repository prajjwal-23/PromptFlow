"""
Event Bus Implementation

This module provides the event bus for publishing and subscribing to events
with enterprise-grade patterns including async processing, error handling,
and performance monitoring.
"""

from __future__ import annotations
import asyncio
import weakref
from typing import Dict, Any, List, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
import threading
from collections import defaultdict
import time

from ..domain.execution.models import ExecutionEvent, EventType
from ..core.logging import get_logger

logger = get_logger(__name__)


class HandlerPriority(str, Enum):
    """Handler priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EventBusConfig:
    """Configuration for event bus."""
    max_handlers: int = 1000
    enable_metrics: bool = True
    enable_tracing: bool = True
    default_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_size: int = 100
    enable_dead_letter_queue: bool = True
    dead_letter_max_size: int = 1000


@dataclass
class HandlerRegistration:
    """Event handler registration information."""
    handler_id: str
    handler: Callable
    event_type: Optional[EventType] = None
    priority: HandlerPriority = HandlerPriority.NORMAL
    filter_func: Optional[Callable[[ExecutionEvent], bool]] = None
    max_retries: int = 3
    timeout: float = 30.0
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    call_count: int = 0
    error_count: int = 0
    last_called: Optional[datetime] = None
    last_error: Optional[str] = None


class DeadLetterQueue:
    """Dead letter queue for failed events."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize dead letter queue."""
        self._max_size = max_size
        self._events: List[tuple[ExecutionEvent, Exception, datetime]] = []
        self._lock = threading.Lock()
    
    def add_event(self, event: ExecutionEvent, error: Exception) -> None:
        """Add failed event to dead letter queue."""
        with self._lock:
            if len(self._events) >= self._max_size:
                # Remove oldest event
                self._events.pop(0)
            
            self._events.append((event, error, datetime.now(timezone.utc)))
            logger.warning(f"Added event {event.event_id} to dead letter queue: {error}")
    
    def get_events(self) -> List[tuple[ExecutionEvent, Exception, datetime]]:
        """Get all events in dead letter queue."""
        with self._lock:
            return self._events.copy()
    
    def clear(self) -> int:
        """Clear dead letter queue and return count of cleared events."""
        with self._lock:
            count = len(self._events)
            self._events.clear()
            return count
    
    def size(self) -> int:
        """Get size of dead letter queue."""
        with self._lock:
            return len(self._events)


class EventBus:
    """Enterprise-grade event bus for publishing and subscribing to events."""
    
    def __init__(self, config: Optional[EventBusConfig] = None):
        """
        Initialize event bus.
        
        Args:
            config: Event bus configuration
        """
        self._config = config or EventBusConfig()
        self._handlers: Dict[EventType, List[HandlerRegistration]] = defaultdict(list)
        self._global_handlers: List[HandlerRegistration] = []
        self._dead_letter_queue = DeadLetterQueue(self._config.dead_letter_max_size)
        self._lock = asyncio.Lock()
        self._metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_called": 0,
            "handler_errors": 0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
            "dead_letter_count": 0,
        }
        self._logger = get_logger(f"{__name__}.EventBus")
        
        # Performance tracking
        self._processing_times: List[float] = []
        self._max_processing_times = 1000
    
    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        priority: HandlerPriority = HandlerPriority.NORMAL,
        filter_func: Optional[Callable[[ExecutionEvent], bool]] = None,
        max_retries: int = 3,
        timeout: float = 30.0
    ) -> str:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Event handler function
            priority: Handler priority
            filter_func: Optional filter function
            max_retries: Maximum retry attempts
            timeout: Handler timeout
            
        Returns:
            Handler registration ID
        """
        async with self._lock:
            if len(self._handlers[event_type]) >= self._config.max_handlers:
                raise ValueError(f"Maximum handlers ({self._config.max_handlers}) reached for {event_type}")
            
            registration = HandlerRegistration(
                handler_id=str(uuid4()),
                handler=handler,
                event_type=event_type,
                priority=priority,
                filter_func=filter_func,
                max_retries=max_retries,
                timeout=timeout
            )
            
            # Insert handler based on priority
            self._insert_handler_by_priority(self._handlers[event_type], registration)
            
            self._logger.info(f"Subscribed handler {registration.handler_id} to {event_type}")
            return registration.handler_id
    
    async def subscribe_all(
        self,
        handler: Callable,
        priority: HandlerPriority = HandlerPriority.NORMAL,
        filter_func: Optional[Callable[[ExecutionEvent], bool]] = None,
        max_retries: int = 3,
        timeout: float = 30.0
    ) -> str:
        """
        Subscribe to all events.
        
        Args:
            handler: Event handler function
            priority: Handler priority
            filter_func: Optional filter function
            max_retries: Maximum retry attempts
            timeout: Handler timeout
            
        Returns:
            Handler registration ID
        """
        async with self._lock:
            if len(self._global_handlers) >= self._config.max_handlers:
                raise ValueError(f"Maximum global handlers ({self._config.max_handlers}) reached")
            
            registration = HandlerRegistration(
                handler_id=str(uuid4()),
                handler=handler,
                priority=priority,
                filter_func=filter_func,
                max_retries=max_retries,
                timeout=timeout
            )
            
            # Insert handler based on priority
            self._insert_handler_by_priority(self._global_handlers, registration)
            
            self._logger.info(f"Subscribed global handler {registration.handler_id}")
            return registration.handler_id
    
    def _insert_handler_by_priority(
        self, 
        handlers: List[HandlerRegistration], 
        registration: HandlerRegistration
    ) -> None:
        """Insert handler in list based on priority."""
        priority_order = {
            HandlerPriority.CRITICAL: 0,
            HandlerPriority.HIGH: 1,
            HandlerPriority.NORMAL: 2,
            HandlerPriority.LOW: 3,
        }
        
        registration_priority = priority_order[registration.priority]
        
        # Find insertion point
        insert_index = len(handlers)
        for i, handler in enumerate(handlers):
            handler_priority = priority_order[handler.priority]
            if registration_priority < handler_priority:
                insert_index = i
                break
        
        handlers.insert(insert_index, registration)
    
    async def unsubscribe(self, handler_id: str) -> bool:
        """
        Unsubscribe handler by ID.
        
        Args:
            handler_id: Handler registration ID
            
        Returns:
            True if handler was found and removed, False otherwise
        """
        async with self._lock:
            # Search in type-specific handlers
            for event_type, handlers in self._handlers.items():
                for i, handler in enumerate(handlers):
                    if handler.handler_id == handler_id:
                        handlers.pop(i)
                        self._logger.info(f"Unsubscribed handler {handler_id} from {event_type}")
                        return True
            
            # Search in global handlers
            for i, handler in enumerate(self._global_handlers):
                if handler.handler_id == handler_id:
                    self._global_handlers.pop(i)
                    self._logger.info(f"Unsubscribed global handler {handler_id}")
                    return True
            
            return False
    
    async def publish(self, event: ExecutionEvent) -> int:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: Event to publish
            
        Returns:
            Number of handlers that processed the event
        """
        start_time = time.time()
        
        try:
            self._metrics["events_published"] += 1
            
            # Get relevant handlers
            handlers = await self._get_handlers_for_event(event)
            
            if not handlers:
                self._logger.debug(f"No handlers for event {event.event_type}")
                return 0
            
            # Process handlers concurrently
            tasks = []
            for registration in handlers:
                if registration.enabled:
                    task = self._call_handler(registration, event)
                    tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful processing
                successful = sum(1 for result in results if not isinstance(result, Exception))
                failed = len(results) - successful
                
                self._metrics["events_processed"] += successful
                self._metrics["events_failed"] += failed
                self._metrics["handlers_called"] += successful
                
                return successful
            else:
                return 0
                
        except Exception as e:
            self._logger.error(f"Error publishing event {event.event_id}: {e}")
            self._metrics["events_failed"] += 1
            raise
        finally:
            # Update processing time metrics
            processing_time = time.time() - start_time
            self._update_processing_time_metrics(processing_time)
    
    async def _get_handlers_for_event(self, event: ExecutionEvent) -> List[HandlerRegistration]:
        """Get all handlers that should receive this event."""
        handlers = []
        
        # Add global handlers
        for registration in self._global_handlers:
            if registration.enabled and self._should_call_handler(registration, event):
                handlers.append(registration)
        
        # Add type-specific handlers
        event_handlers = self._handlers.get(event.event_type, [])
        for registration in event_handlers:
            if registration.enabled and self._should_call_handler(registration, event):
                handlers.append(registration)
        
        return handlers
    
    def _should_call_handler(self, registration: HandlerRegistration, event: ExecutionEvent) -> bool:
        """Check if handler should be called for this event."""
        if registration.filter_func:
            try:
                return registration.filter_func(event)
            except Exception as e:
                self._logger.error(f"Error in filter function for handler {registration.handler_id}: {e}")
                return False
        return True
    
    async def _call_handler(self, registration: HandlerRegistration, event: ExecutionEvent) -> None:
        """Call a single handler with retry logic."""
        last_exception = None
        
        for attempt in range(registration.max_retries + 1):
            try:
                # Update handler metadata
                registration.call_count += 1
                registration.last_called = datetime.now(timezone.utc)
                
                # Call handler with timeout
                if asyncio.iscoroutinefunction(registration.handler):
                    await asyncio.wait_for(
                        registration.handler(event),
                        timeout=registration.timeout
                    )
                else:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, registration.handler, event),
                        timeout=registration.timeout
                    )
                
                # Clear any previous error
                registration.last_error = None
                return
                
            except asyncio.TimeoutError:
                last_exception = f"Handler {registration.handler_id} timed out after {registration.timeout}s"
                self._logger.warning(f"Timeout in handler {registration.handler_id} (attempt {attempt + 1})")
                
            except Exception as e:
                last_exception = str(e)
                registration.last_error = last_exception
                registration.error_count += 1
                self._logger.error(f"Error in handler {registration.handler_id} (attempt {attempt + 1}): {e}")
                
                if attempt < registration.max_retries:
                    await asyncio.sleep(self._config.retry_delay * (2 ** attempt))
        
        # All retries failed
        self._metrics["handler_errors"] += 1
        
        if self._config.enable_dead_letter_queue:
            self._dead_letter_queue.add_event(event, Exception(last_exception or "Unknown error"))
            self._metrics["dead_letter_count"] += 1
    
    def _update_processing_time_metrics(self, processing_time: float) -> None:
        """Update processing time metrics."""
        if not self._config.enable_metrics:
            return
        
        self._processing_times.append(processing_time)
        
        # Keep only recent processing times
        if len(self._processing_times) > self._max_processing_times:
            self._processing_times.pop(0)
        
        # Update metrics
        self._metrics["total_processing_time"] += processing_time
        if self._metrics["events_published"] > 0:
            self._metrics["average_processing_time"] = (
                self._metrics["total_processing_time"] / self._metrics["events_published"]
            )
    
    async def publish_batch(self, events: List[ExecutionEvent]) -> Dict[str, int]:
        """
        Publish multiple events in batch.
        
        Args:
            events: List of events to publish
            
        Returns:
            Dictionary with processing statistics
        """
        results = {
            "total": len(events),
            "successful": 0,
            "failed": 0,
            "handlers_called": 0,
        }
        
        # Process events in batches
        batch_size = self._config.batch_size
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            
            try:
                # Process batch concurrently
                tasks = [self.publish(event) for event in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        results["failed"] += 1
                    else:
                        results["successful"] += 1
                        results["handlers_called"] += result
                        
            except Exception as e:
                self._logger.error(f"Error processing batch: {e}")
                results["failed"] += len(batch)
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        metrics = self._metrics.copy()
        
        # Add additional metrics
        metrics["handlers_count"] = sum(len(handlers) for handlers in self._handlers.values())
        metrics["global_handlers_count"] = len(self._global_handlers)
        metrics["dead_letter_size"] = self._dead_letter_queue.size()
        
        # Calculate success rate
        total_events = metrics["events_processed"] + metrics["events_failed"]
        if total_events > 0:
            metrics["success_rate"] = (metrics["events_processed"] / total_events) * 100
        else:
            metrics["success_rate"] = 0.0
        
        # Add processing time statistics
        if self._processing_times:
            metrics["min_processing_time"] = min(self._processing_times)
            metrics["max_processing_time"] = max(self._processing_times)
            metrics["median_processing_time"] = sorted(self._processing_times)[len(self._processing_times) // 2]
        
        return metrics
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about registered handlers."""
        info = {
            "type_handlers": {},
            "global_handlers": [],
            "total_handlers": 0,
        }
        
        # Type-specific handlers
        for event_type, handlers in self._handlers.items():
            info["type_handlers"][event_type.value] = [
                {
                    "handler_id": h.handler_id,
                    "priority": h.priority.value,
                    "enabled": h.enabled,
                    "call_count": h.call_count,
                    "error_count": h.error_count,
                    "last_called": h.last_called.isoformat() if h.last_called else None,
                    "last_error": h.last_error,
                }
                for h in handlers
            ]
            info["total_handlers"] += len(handlers)
        
        # Global handlers
        info["global_handlers"] = [
            {
                "handler_id": h.handler_id,
                "priority": h.priority.value,
                "enabled": h.enabled,
                "call_count": h.call_count,
                "error_count": h.error_count,
                "last_called": h.last_called.isoformat() if h.last_called else None,
                "last_error": h.last_error,
            }
            for h in self._global_handlers
        ]
        info["total_handlers"] += len(self._global_handlers)
        
        return info
    
    def get_dead_letter_events(self) -> List[tuple[ExecutionEvent, Exception, datetime]]:
        """Get events in dead letter queue."""
        return self._dead_letter_queue.get_events()
    
    async def clear_dead_letter_queue(self) -> int:
        """Clear dead letter queue."""
        count = self._dead_letter_queue.clear()
        self._metrics["dead_letter_count"] = 0
        self._logger.info(f"Cleared {count} events from dead letter queue")
        return count
    
    async def enable_handler(self, handler_id: str) -> bool:
        """Enable a handler."""
        async with self._lock:
            return self._set_handler_enabled(handler_id, True)
    
    async def disable_handler(self, handler_id: str) -> bool:
        """Disable a handler."""
        async with self._lock:
            return self._set_handler_enabled(handler_id, False)
    
    def _set_handler_enabled(self, handler_id: str, enabled: bool) -> bool:
        """Set handler enabled status."""
        # Search in type-specific handlers
        for handlers in self._handlers.values():
            for handler in handlers:
                if handler.handler_id == handler_id:
                    handler.enabled = enabled
                    self._logger.info(f"{'Enabled' if enabled else 'Disabled'} handler {handler_id}")
                    return True
        
        # Search in global handlers
        for handler in self._global_handlers:
            if handler.handler_id == handler_id:
                handler.enabled = enabled
                self._logger.info(f"{'Enabled' if enabled else 'Disabled'} global handler {handler_id}")
                return True
        
        return False
    
    async def shutdown(self) -> None:
        """Shutdown event bus and cleanup resources."""
        self._logger.info("Shutting down event bus")
        
        # Clear all handlers
        async with self._lock:
            self._handlers.clear()
            self._global_handlers.clear()
        
        # Clear dead letter queue
        self._dead_letter_queue.clear()
        
        self._logger.info("Event bus shutdown complete")


# Global event bus instance
_default_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the default event bus instance."""
    global _default_event_bus
    if _default_event_bus is None:
        _default_event_bus = EventBus()
    return _default_event_bus


def configure_event_bus(config: EventBusConfig) -> EventBus:
    """Configure and return a new event bus instance."""
    return EventBus(config)


# Decorator for event handlers
def event_handler(
    event_type: Optional[EventType] = None,
    priority: HandlerPriority = HandlerPriority.NORMAL,
    max_retries: int = 3,
    timeout: float = 30.0
):
    """Decorator for registering event handlers."""
    def decorator(func):
        func._event_handler_config = {
            "event_type": event_type,
            "priority": priority,
            "max_retries": max_retries,
            "timeout": timeout,
        }
        return func
    return decorator


# Convenience function for subscribing to events
async def subscribe_to_events(
    event_type: EventType,
    handler: Callable,
    **kwargs
) -> str:
    """Subscribe to events using the default event bus."""
    event_bus = get_event_bus()
    return await event_bus.subscribe(event_type, handler, **kwargs)


# Convenience function for publishing events
async def publish_event(event: ExecutionEvent) -> int:
    """Publish event using the default event bus."""
    event_bus = get_event_bus()
    return await event_bus.publish(event)