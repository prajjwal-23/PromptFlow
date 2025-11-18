"""
Service Factory Implementation

This module provides the concrete implementation of the ServiceFactory
interface for creating service instances with dependency injection.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
import logging

from app.domain.execution.services import (
    ServiceFactory,
    ExecutionService,
    GraphCompilerService,
    NodeExecutorService,
    StreamingService,
    LLMService,
    ResourceManagementService,
    MonitoringService,
    CacheService,
    SecurityService,
    NotificationService
)
from app.execution.store.factory import create_repository_provider
from app.execution.services.execution_service import ExecutionServiceImpl
from app.execution.services.streaming_service import StreamingServiceImpl
from app.llm.service import LLMService as LLMServiceImpl
from app.core.logging import get_logger

logger = get_logger(__name__)


class ServiceFactoryImpl(ServiceFactory):
    """Concrete implementation of ServiceFactory."""
    
    def __init__(self):
        """Initialize service factory."""
        self.logger = logger
        self.repository_provider = create_repository_provider()
        self._service_cache: Dict[str, Any] = {}
    
    def create_execution_service(self) -> ExecutionService:
        """Create execution service instance."""
        try:
            if "execution_service" not in self._service_cache:
                self._service_cache["execution_service"] = ExecutionServiceImpl(
                    repository_provider=self.repository_provider
                )
            
            return self._service_cache["execution_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating execution service: {e}")
            raise
    
    def create_graph_compiler_service(self) -> GraphCompilerService:
        """Create graph compiler service instance."""
        try:
            # This would be implemented when we create the graph compiler service
            # For now, return a placeholder
            from app.execution.compiler.dag_compiler import DAGCompiler
            
            if "graph_compiler_service" not in self._service_cache:
                # Placeholder implementation
                class GraphCompilerServiceImpl:
                    def __init__(self):
                        self.compiler = DAGCompiler()
                    
                    async def compile_graph(self, graph_json, execution_config):
                        return await self.compiler.compile(graph_json)
                    
                    async def validate_graph(self, graph_json):
                        return await self.compiler.validate(graph_json)
                    
                    async def optimize_graph(self, dag):
                        return await self.compiler.optimize(dag)
                    
                    async def estimate_execution_time(self, dag):
                        return await self.compiler.estimate_time(dag)
                    
                    async def estimate_resource_requirements(self, dag):
                        return await self.compiler.estimate_resources(dag)
                
                self._service_cache["graph_compiler_service"] = GraphCompilerServiceImpl()
            
            return self._service_cache["graph_compiler_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating graph compiler service: {e}")
            raise
    
    def create_node_executor_service(self) -> NodeExecutorService:
        """Create node executor service instance."""
        try:
            # This would be implemented when we create the node executor service
            # For now, return a placeholder
            if "node_executor_service" not in self._service_cache:
                # Placeholder implementation
                class NodeExecutorServiceImpl:
                    def __init__(self):
                        pass
                    
                    async def execute_node(self, node_id, node_type, config, inputs, context):
                        # Placeholder implementation
                        from app.domain.execution.models import NodeOutput, NodeStatus
                        return NodeOutput(
                            node_id=node_id,
                            status=NodeStatus.COMPLETED,
                            data={"result": f"Executed {node_type} node"},
                            execution_time=0.1
                        )
                    
                    async def validate_node_inputs(self, node_type, inputs):
                        return {"valid": True}
                    
                    async def get_node_schema(self, node_type):
                        return {"input_schema": {}, "output_schema": {}}
                    
                    async def cleanup_node_resources(self, node_id):
                        pass
                
                self._service_cache["node_executor_service"] = NodeExecutorServiceImpl()
            
            return self._service_cache["node_executor_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating node executor service: {e}")
            raise
    
    def create_streaming_service(self) -> StreamingService:
        """Create streaming service instance."""
        try:
            if "streaming_service" not in self._service_cache:
                self._service_cache["streaming_service"] = StreamingServiceImpl()
            
            return self._service_cache["streaming_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating streaming service: {e}")
            raise
    
    def create_llm_service(self) -> LLMService:
        """Create LLM service instance."""
        try:
            if "llm_service" not in self._service_cache:
                self._service_cache["llm_service"] = LLMServiceImpl()
            
            return self._service_cache["llm_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating LLM service: {e}")
            raise
    
    def create_resource_management_service(self) -> ResourceManagementService:
        """Create resource management service instance."""
        try:
            # This would be implemented when we create the resource management service
            # For now, return a placeholder
            if "resource_management_service" not in self._service_cache:
                # Placeholder implementation
                class ResourceManagementServiceImpl:
                    def __init__(self):
                        pass
                    
                    async def allocate_resources(self, execution_id, requirements):
                        return True
                    
                    async def release_resources(self, execution_id):
                        pass
                    
                    async def check_resource_availability(self, requirements):
                        return True
                    
                    async def get_resource_usage(self, execution_id):
                        return {"cpu": 0.5, "memory": 512}
                    
                    async def get_system_resources(self):
                        return {"cpu_cores": 8, "memory_mb": 16384}
                
                self._service_cache["resource_management_service"] = ResourceManagementServiceImpl()
            
            return self._service_cache["resource_management_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating resource management service: {e}")
            raise
    
    def create_monitoring_service(self) -> MonitoringService:
        """Create monitoring service instance."""
        try:
            # This would be implemented when we create the monitoring service
            # For now, return a placeholder
            if "monitoring_service" not in self._service_cache:
                # Placeholder implementation
                class MonitoringServiceImpl:
                    def __init__(self):
                        pass
                    
                    async def record_execution_metric(self, execution_id, metric_name, value, tags=None):
                        pass
                    
                    async def record_node_metric(self, execution_id, node_id, metric_name, value, tags=None):
                        pass
                    
                    async def get_execution_metrics(self, execution_id):
                        return {}
                    
                    async def get_system_metrics(self):
                        return {}
                    
                    async def create_alert(self, alert_type, message, severity, metadata=None):
                        pass
                
                self._service_cache["monitoring_service"] = MonitoringServiceImpl()
            
            return self._service_cache["monitoring_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating monitoring service: {e}")
            raise
    
    def create_cache_service(self) -> CacheService:
        """Create cache service instance."""
        try:
            # This would be implemented when we create the cache service
            # For now, return a placeholder
            if "cache_service" not in self._service_cache:
                # Placeholder implementation
                class CacheServiceImpl:
                    def __init__(self):
                        self._cache = {}
                    
                    async def get(self, key, default=None):
                        return self._cache.get(key, default)
                    
                    async def set(self, key, value, ttl=None):
                        self._cache[key] = value
                    
                    async def delete(self, key):
                        return self._cache.pop(key, None) is not None
                    
                    async def clear_pattern(self, pattern):
                        # Simple pattern matching for keys starting with pattern
                        keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
                        for key in keys_to_delete:
                            del self._cache[key]
                        return len(keys_to_delete)
                    
                    async def get_stats(self):
                        return {"keys": len(self._cache)}
                
                self._service_cache["cache_service"] = CacheServiceImpl()
            
            return self._service_cache["cache_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating cache service: {e}")
            raise
    
    def create_security_service(self) -> SecurityService:
        """Create security service instance."""
        try:
            # This would be implemented when we create the security service
            # For now, return a placeholder
            if "security_service" not in self._service_cache:
                # Placeholder implementation
                class SecurityServiceImpl:
                    def __init__(self):
                        pass
                    
                    async def validate_access(self, user_id, resource_id, action):
                        return True
                    
                    async def encrypt_sensitive_data(self, data):
                        return data  # Placeholder
                    
                    async def decrypt_sensitive_data(self, encrypted_data):
                        return encrypted_data  # Placeholder
                    
                    async def audit_log(self, action, user_id, resource_id, metadata=None):
                        pass
                
                self._service_cache["security_service"] = SecurityServiceImpl()
            
            return self._service_cache["security_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating security service: {e}")
            raise
    
    def create_notification_service(self) -> NotificationService:
        """Create notification service instance."""
        try:
            # This would be implemented when we create the notification service
            # For now, return a placeholder
            if "notification_service" not in self._service_cache:
                # Placeholder implementation
                class NotificationServiceImpl:
                    def __init__(self):
                        pass
                    
                    async def send_execution_notification(self, execution_id, notification_type, message, recipients):
                        pass
                    
                    async def send_error_notification(self, execution_id, error, recipients):
                        pass
                    
                    async def send_completion_notification(self, execution_id, metrics, recipients):
                        pass
                
                self._service_cache["notification_service"] = NotificationServiceImpl()
            
            return self._service_cache["notification_service"]
            
        except Exception as e:
            self.logger.error(f"Error creating notification service: {e}")
            raise
    
    async def create_all_services(self) -> Dict[str, Any]:
        """Create all service instances."""
        try:
            return {
                "execution": self.create_execution_service(),
                "graph_compiler": self.create_graph_compiler_service(),
                "node_executor": self.create_node_executor_service(),
                "streaming": self.create_streaming_service(),
                "llm": self.create_llm_service(),
                "resource_management": self.create_resource_management_service(),
                "monitoring": self.create_monitoring_service(),
                "cache": self.create_cache_service(),
                "security": self.create_security_service(),
                "notification": self.create_notification_service(),
            }
            
        except Exception as e:
            self.logger.error(f"Error creating all services: {e}")
            raise
    
    def clear_cache(self) -> None:
        """Clear service cache."""
        try:
            self._service_cache.clear()
            self.logger.info("Service cache cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing service cache: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        try:
            services = await self.create_all_services()
            health_status = {
                "overall": "healthy",
                "services": {}
            }
            
            for name, service in services.items():
                try:
                    # Check if service has health check method
                    if hasattr(service, 'health_check'):
                        service_health = await service.health_check()
                        health_status["services"][name] = service_health
                        
                        if service_health.get("status") != "healthy":
                            health_status["overall"] = "unhealthy"
                    else:
                        health_status["services"][name] = {
                            "status": "healthy",
                            "message": "No health check method available"
                        }
                        
                except Exception as e:
                    health_status["services"][name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health_status["overall"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error in service health check: {e}")
            return {
                "overall": "unhealthy",
                "error": str(e)
            }


# Global service factory instance
_service_factory: Optional[ServiceFactoryImpl] = None


def get_service_factory() -> ServiceFactoryImpl:
    """Get the global service factory."""
    global _service_factory
    
    if _service_factory is None:
        _service_factory = ServiceFactoryImpl()
    
    return _service_factory


def create_service_factory() -> ServiceFactoryImpl:
    """Create a new service factory instance."""
    return ServiceFactoryImpl()


# Service provider for dependency injection
class ServiceProvider:
    """Provider for service instances with dependency injection."""
    
    def __init__(self, factory: Optional[ServiceFactoryImpl] = None):
        """Initialize provider with factory."""
        self.factory = factory or get_service_factory()
        self.logger = logger
    
    def get_execution_service(self) -> ExecutionService:
        """Get execution service."""
        return self.factory.create_execution_service()
    
    def get_graph_compiler_service(self) -> GraphCompilerService:
        """Get graph compiler service."""
        return self.factory.create_graph_compiler_service()
    
    def get_node_executor_service(self) -> NodeExecutorService:
        """Get node executor service."""
        return self.factory.create_node_executor_service()
    
    def get_streaming_service(self) -> StreamingService:
        """Get streaming service."""
        return self.factory.create_streaming_service()
    
    def get_llm_service(self) -> LLMService:
        """Get LLM service."""
        return self.factory.create_llm_service()
    
    def get_resource_management_service(self) -> ResourceManagementService:
        """Get resource management service."""
        return self.factory.create_resource_management_service()
    
    def get_monitoring_service(self) -> MonitoringService:
        """Get monitoring service."""
        return self.factory.create_monitoring_service()
    
    def get_cache_service(self) -> CacheService:
        """Get cache service."""
        return self.factory.create_cache_service()
    
    def get_security_service(self) -> SecurityService:
        """Get security service."""
        return self.factory.create_security_service()
    
    def get_notification_service(self) -> NotificationService:
        """Get notification service."""
        return self.factory.create_notification_service()
    
    async def get_all_services(self) -> Dict[str, Any]:
        """Get all services."""
        return await self.factory.create_all_services()


# Factory functions for easy access
def create_service_provider() -> ServiceProvider:
    """Create service provider."""
    return ServiceProvider()


def get_service_provider() -> ServiceProvider:
    """Get global service provider."""
    return ServiceProvider()