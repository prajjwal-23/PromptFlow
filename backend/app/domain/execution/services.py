"""
Service Interfaces for Execution Domain

This module defines service interfaces following Clean Architecture principles.
All services are designed for dependency injection, testability, and single responsibility.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union, Callable, AsyncIterator
from datetime import datetime
from uuid import UUID

from .models import (
    Execution, 
    ExecutionEvent, 
    NodeOutput, 
    ExecutionStatus, 
    NodeStatus,
    ExecutionConfig,
    ExecutionInput,
    ResourceRequirement,
    ExecutionMetrics
)
from .repositories import (
    ExecutionRepository,
    EventRepository,
    NodeOutputRepository,
    CacheRepository,
    LockRepository,
    MetricsRepository,
    UnitOfWork
)


class ExecutionService(ABC):
    """Service interface for execution management."""
    
    @abstractmethod
    async def create_execution(
        self,
        agent_id: str,
        input_data: ExecutionInput,
        config: Optional[ExecutionConfig] = None
    ) -> Execution:
        """Create a new execution."""
        pass
    
    @abstractmethod
    async def start_execution(self, execution_id: str) -> Execution:
        """Start an execution."""
        pass
    
    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an execution."""
        pass
    
    @abstractmethod
    async def pause_execution(self, execution_id: str) -> bool:
        """Pause an execution."""
        pass
    
    @abstractmethod
    async def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused execution."""
        pass
    
    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID."""
        pass
    
    @abstractmethod
    async def list_executions(
        self,
        agent_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Execution]:
        """List executions with optional filters."""
        pass
    
    @abstractmethod
    async def get_execution_metrics(
        self,
        execution_id: str
    ) -> Optional[ExecutionMetrics]:
        """Get execution metrics."""
        pass


class GraphCompilerService(ABC):
    """Service interface for graph compilation."""
    
    @abstractmethod
    async def compile_graph(
        self,
        graph_json: Dict[str, Any],
        execution_config: ExecutionConfig
    ) -> Any:  # DAG type
        """Compile JSON graph to executable DAG."""
        pass
    
    @abstractmethod
    async def validate_graph(
        self,
        graph_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate graph structure and business rules."""
        pass
    
    @abstractmethod
    async def optimize_graph(
        self,
        dag: Any  # DAG type
    ) -> Any:  # Optimized DAG type
        """Optimize DAG for execution performance."""
        pass
    
    @abstractmethod
    async def estimate_execution_time(
        self,
        dag: Any  # DAG type
    ) -> float:
        """Estimate execution time in seconds."""
        pass
    
    @abstractmethod
    async def estimate_resource_requirements(
        self,
        dag: Any  # DAG type
    ) -> ResourceRequirement:
        """Estimate resource requirements."""
        pass


class NodeExecutorService(ABC):
    """Service interface for node execution."""
    
    @abstractmethod
    async def execute_node(
        self,
        node_id: str,
        node_type: str,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> NodeOutput:
        """Execute a single node."""
        pass
    
    @abstractmethod
    async def validate_node_inputs(
        self,
        node_type: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate node inputs."""
        pass
    
    @abstractmethod
    async def get_node_schema(
        self,
        node_type: str
    ) -> Dict[str, Any]:
        """Get node input/output schema."""
        pass
    
    @abstractmethod
    async def cleanup_node_resources(
        self,
        node_id: str
    ) -> None:
        """Clean up resources after node execution."""
        pass


class StreamingService(ABC):
    """Service interface for real-time streaming."""
    
    @abstractmethod
    async def start_stream(
        self,
        execution_id: str,
        client_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Start streaming events for an execution."""
        pass
    
    @abstractmethod
    async def send_event(
        self,
        execution_id: str,
        event: ExecutionEvent
    ) -> None:
        """Send event to stream."""
        pass
    
    @abstractmethod
    async def subscribe_to_execution(
        self,
        execution_id: str,
        callback: Callable[[ExecutionEvent], None]
    ) -> str:
        """Subscribe to execution events. Returns subscription ID."""
        pass
    
    @abstractmethod
    async def unsubscribe_from_execution(
        self,
        execution_id: str,
        subscription_id: str
    ) -> bool:
        """Unsubscribe from execution events."""
        pass
    
    @abstractmethod
    async def get_active_streams(self) -> List[str]:
        """Get list of active stream IDs."""
        pass


class LLMService(ABC):
    """Service interface for LLM provider integrations."""
    
    @abstractmethod
    async def generate_completion(
        self,
        provider: str,
        model: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Union[str, AsyncIterator[str]]:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def get_available_models(self, provider: str) -> List[Dict[str, Any]]:
        """Get available models for a provider."""
        pass
    
    @abstractmethod
    async def validate_model_access(
        self,
        provider: str,
        model: str
    ) -> bool:
        """Validate if model is accessible."""
        pass
    
    @abstractmethod
    async def get_token_count(
        self,
        provider: str,
        model: str,
        text: str
    ) -> int:
        """Get token count for text."""
        pass
    
    @abstractmethod
    async def estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Estimate cost in USD."""
        pass


class ResourceManagementService(ABC):
    """Service interface for resource management."""
    
    @abstractmethod
    async def allocate_resources(
        self,
        execution_id: str,
        requirements: ResourceRequirement
    ) -> bool:
        """Allocate resources for execution."""
        pass
    
    @abstractmethod
    async def release_resources(
        self,
        execution_id: str
    ) -> None:
        """Release resources for execution."""
        pass
    
    @abstractmethod
    async def check_resource_availability(
        self,
        requirements: ResourceRequirement
    ) -> bool:
        """Check if resources are available."""
        pass
    
    @abstractmethod
    async def get_resource_usage(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """Get current resource usage."""
        pass
    
    @abstractmethod
    async def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information."""
        pass


class MonitoringService(ABC):
    """Service interface for monitoring and metrics."""
    
    @abstractmethod
    async def record_execution_metric(
        self,
        execution_id: str,
        metric_name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record execution metric."""
        pass
    
    @abstractmethod
    async def record_node_metric(
        self,
        execution_id: str,
        node_id: str,
        metric_name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record node execution metric."""
        pass
    
    @abstractmethod
    async def get_execution_metrics(
        self,
        execution_id: str
    ) -> Dict[str, Any]:
        """Get all metrics for an execution."""
        pass
    
    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        pass
    
    @abstractmethod
    async def create_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create an alert."""
        pass


class CacheService(ABC):
    """Service interface for caching."""
    
    @abstractmethod
    async def get(
        self,
        key: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear_pattern(
        self,
        pattern: str
    ) -> int:
        """Delete keys matching pattern. Returns count of deleted keys."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class SecurityService(ABC):
    """Service interface for security operations."""
    
    @abstractmethod
    async def validate_access(
        self,
        user_id: str,
        resource_id: str,
        action: str
    ) -> bool:
        """Validate user access to resource."""
        pass
    
    @abstractmethod
    async def encrypt_sensitive_data(
        self,
        data: str
    ) -> str:
        """Encrypt sensitive data."""
        pass
    
    @abstractmethod
    async def decrypt_sensitive_data(
        self,
        encrypted_data: str
    ) -> str:
        """Decrypt sensitive data."""
        pass
    
    @abstractmethod
    async def audit_log(
        self,
        action: str,
        user_id: str,
        resource_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit trail."""
        pass


class NotificationService(ABC):
    """Service interface for notifications."""
    
    @abstractmethod
    async def send_execution_notification(
        self,
        execution_id: str,
        notification_type: str,
        message: str,
        recipients: List[str]
    ) -> None:
        """Send execution notification."""
        pass
    
    @abstractmethod
    async def send_error_notification(
        self,
        execution_id: str,
        error: str,
        recipients: List[str]
    ) -> None:
        """Send error notification."""
        pass
    
    @abstractmethod
    async def send_completion_notification(
        self,
        execution_id: str,
        metrics: ExecutionMetrics,
        recipients: List[str]
    ) -> None:
        """Send completion notification."""
        pass


# Service factory interface
class ServiceFactory(ABC):
    """Factory interface for creating service instances."""
    
    @abstractmethod
    def create_execution_service(self) -> ExecutionService:
        """Create execution service instance."""
        pass
    
    @abstractmethod
    def create_graph_compiler_service(self) -> GraphCompilerService:
        """Create graph compiler service instance."""
        pass
    
    @abstractmethod
    def create_node_executor_service(self) -> NodeExecutorService:
        """Create node executor service instance."""
        pass
    
    @abstractmethod
    def create_streaming_service(self) -> StreamingService:
        """Create streaming service instance."""
        pass
    
    @abstractmethod
    def create_llm_service(self) -> LLMService:
        """Create LLM service instance."""
        pass
    
    @abstractmethod
    def create_resource_management_service(self) -> ResourceManagementService:
        """Create resource management service instance."""
        pass
    
    @abstractmethod
    def create_monitoring_service(self) -> MonitoringService:
        """Create monitoring service instance."""
        pass
    
    @abstractmethod
    def create_cache_service(self) -> CacheService:
        """Create cache service instance."""
        pass
    
    @abstractmethod
    def create_security_service(self) -> SecurityService:
        """Create security service instance."""
        pass
    
    @abstractmethod
    def create_notification_service(self) -> NotificationService:
        """Create notification service instance."""
        pass


# Configuration interfaces
class ServiceConfig(ABC):
    """Configuration interface for services."""
    
    @abstractmethod
    def get_llm_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get LLM provider configurations."""
        pass
    
    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        pass
    
    @abstractmethod
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        pass
    
    @abstractmethod
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        pass
    
    @abstractmethod
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration."""
        pass


# Health check interface
class HealthCheckService(ABC):
    """Service interface for health checks."""
    
    @abstractmethod
    async def check_service_health(self) -> Dict[str, Any]:
        """Check overall service health."""
        pass
    
    @abstractmethod
    async def check_dependencies_health(self) -> Dict[str, Any]:
        """Check health of all dependencies."""
        pass
    
    @abstractmethod
    async def get_health_status(self) -> str:
        """Get overall health status."""
        pass