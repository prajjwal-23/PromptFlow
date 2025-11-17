"""
Node Factory Implementation

This module provides the node factory for creating node instances
with dependency injection and enterprise-grade patterns.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass
from datetime import datetime
import inspect

from ..execution.nodes.base_node import BaseNode, NodeInput, NodeOutput, NodeContext, NodeType, ExecutionMode
from .input_node import InputNode
from .output_node import OutputNode
from .llm_node import LLMNode
from .retrieval_node import RetrievalNode
from .tool_node import ToolNode
from ..domain.execution.models import NodeConfiguration


@dataclass
class NodeFactoryConfig:
    """Node factory configuration."""
    default_execution_mode: ExecutionMode = ExecutionMode.SYNC
    enable_metrics: bool = True
    enable_caching: bool = True
    custom_node_registry: Dict[str, Type[BaseNode]] = None
    dependency_injection_container: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_node_registry is None:
            self.custom_node_registry = {}
        if self.dependency_injection_container is None:
            self.dependency_injection_container = {}


class NodeFactory:
    """Enterprise-grade node factory with dependency injection and plugin architecture."""
    
    def __init__(self, config: Optional[NodeFactoryConfig] = None):
        """
        Initialize the node factory.
        
        Args:
            config: Factory configuration
        """
        self._config = config or NodeFactoryConfig()
        self._node_registry = self._create_default_registry()
        self._node_cache = {} if self._config.enable_caching else None
        self._metrics = {
            "nodes_created": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "creation_time_total": 0.0,
            "average_creation_time": 0.0,
        }
    
    def _create_default_registry(self) -> Dict[NodeType, Type[BaseNode]]:
        """Create default node type registry."""
        return {
            NodeType.INPUT: InputNode,
            NodeType.OUTPUT: OutputNode,
            NodeType.LLM: LLMNode,
            NodeType.RETRIEVAL: RetrievalNode,
            NodeType.TOOL: ToolNode,
        }
    
    def register_node_type(
        self, 
        node_type: NodeType, 
        node_class: Type[BaseNode],
        override: bool = False
    ) -> None:
        """
        Register a new node type.
        
        Args:
            node_type: Node type enum value
            node_class: Node class implementation
            override: Whether to override existing registration
        """
        if node_type in self._node_registry and not override:
            raise ValueError(f"Node type {node_type} is already registered. Use override=True to replace.")
        
        # Validate node class
        if not issubclass(node_class, BaseNode):
            raise ValueError(f"Node class must inherit from BaseNode")
        
        self._node_registry[node_type] = node_class
    
    def register_custom_node(
        self, 
        name: str, 
        node_class: Type[BaseNode],
        override: bool = False
    ) -> None:
        """
        Register a custom node type by name.
        
        Args:
            name: Custom node name
            node_class: Node class implementation
            override: Whether to override existing registration
        """
        if name in self._config.custom_node_registry and not override:
            raise ValueError(f"Custom node {name} is already registered. Use override=True to replace.")
        
        # Validate node class
        if not issubclass(node_class, BaseNode):
            raise ValueError(f"Node class must inherit from BaseNode")
        
        self._config.custom_node_registry[name] = node_class
    
    def unregister_node_type(self, node_type: NodeType) -> None:
        """Unregister a node type."""
        if node_type in self._node_registry:
            del self._node_registry[node_type]
    
    def unregister_custom_node(self, name: str) -> None:
        """Unregister a custom node type."""
        if name in self._config.custom_node_registry:
            del self._config.custom_node_registry[name]
    
    def create_node(
        self,
        node_type: Union[NodeType, str],
        node_id: str,
        config: NodeConfiguration,
        execution_mode: Optional[ExecutionMode] = None,
        **kwargs
    ) -> BaseNode:
        """
        Create a node instance.
        
        Args:
            node_type: Type of node to create (enum or string for custom nodes)
            node_id: Unique identifier for the node
            config: Node configuration
            execution_mode: Execution mode (uses factory default if None)
            **kwargs: Additional arguments for node constructor
            
        Returns:
            Node instance
        """
        start_time = datetime.now()
        
        try:
            # Determine execution mode
            if execution_mode is None:
                execution_mode = self._config.default_execution_mode
            
            # Get node class
            node_class = self._get_node_class(node_type)
            
            # Check cache
            cache_key = None
            if self._node_cache is not None:
                cache_key = self._generate_cache_key(node_type, node_id, config, execution_mode, kwargs)
                if cache_key in self._node_cache:
                    self._metrics["cache_hits"] += 1
                    return self._node_cache[cache_key]
                self._metrics["cache_misses"] += 1
            
            # Prepare constructor arguments
            constructor_args = self._prepare_constructor_args(
                node_class, node_id, config, execution_mode, **kwargs
            )
            
            # Create node instance
            node = node_class(**constructor_args)
            
            # Apply dependency injection
            self._apply_dependency_injection(node)
            
            # Cache the node
            if self._node_cache is not None and cache_key:
                self._node_cache[cache_key] = node
            
            # Update metrics
            creation_time = (datetime.now() - start_time).total_seconds()
            self._metrics["nodes_created"] += 1
            self._metrics["creation_time_total"] += creation_time
            self._metrics["average_creation_time"] = (
                self._metrics["creation_time_total"] / self._metrics["nodes_created"]
            )
            
            return node
            
        except Exception as e:
            raise RuntimeError(f"Failed to create node {node_id} of type {node_type}: {str(e)}") from e
    
    def _get_node_class(self, node_type: Union[NodeType, str]) -> Type[BaseNode]:
        """Get node class for the given type."""
        if isinstance(node_type, NodeType):
            if node_type not in self._node_registry:
                raise ValueError(f"Unknown node type: {node_type}")
            return self._node_registry[node_type]
        elif isinstance(node_type, str):
            if node_type in self._config.custom_node_registry:
                return self._config.custom_node_registry[node_type]
            else:
                # Try to convert string to NodeType enum
                try:
                    enum_type = NodeType(node_type)
                    if enum_type in self._node_registry:
                        return self._node_registry[enum_type]
                except ValueError:
                    pass
                raise ValueError(f"Unknown custom node type: {node_type}")
        else:
            raise ValueError(f"Invalid node type: {node_type}")
    
    def _generate_cache_key(
        self, 
        node_type: Union[NodeType, str], 
        node_id: str, 
        config: NodeConfiguration,
        execution_mode: ExecutionMode,
        kwargs: Dict[str, Any]
    ) -> str:
        """Generate cache key for node instance."""
        # Create a hash of all parameters
        cache_data = {
            "node_type": str(node_type),
            "node_id": node_id,
            "config": config.config if hasattr(config, 'config') else config,
            "execution_mode": execution_mode.value,
            "kwargs": kwargs,
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"node_{hash(cache_str)}"
    
    def _prepare_constructor_args(
        self,
        node_class: Type[BaseNode],
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare constructor arguments for node class."""
        # Get constructor signature
        sig = inspect.signature(node_class.__init__)
        
        # Prepare arguments
        args = {
            "node_id": node_id,
            "config": config,
            "execution_mode": execution_mode,
        }
        
        # Add additional kwargs that match constructor parameters
        for param_name, param in sig.parameters.items():
            if param_name in kwargs and param_name not in args:
                args[param_name] = kwargs[param_name]
        
        return args
    
    def _apply_dependency_injection(self, node: BaseNode) -> None:
        """Apply dependency injection to node instance."""
        if not self._config.dependency_injection_container:
            return
        
        # Inject dependencies based on node type
        for attr_name, dependency in self._config.dependency_injection_container.items():
            if hasattr(node, attr_name):
                setattr(node, attr_name, dependency)
    
    def create_nodes_from_config(
        self,
        nodes_config: List[Dict[str, Any]],
        default_execution_mode: Optional[ExecutionMode] = None
    ) -> Dict[str, BaseNode]:
        """
        Create multiple nodes from configuration.
        
        Args:
            nodes_config: List of node configurations
            default_execution_mode: Default execution mode for all nodes
            
        Returns:
            Dictionary mapping node IDs to node instances
        """
        nodes = {}
        
        for node_config in nodes_config:
            node_id = node_config["id"]
            node_type_str = node_config["type"]
            node_data = node_config.get("data", {})
            
            # Convert string type to NodeType enum
            try:
                node_type = NodeType(node_type_str)
            except ValueError:
                # Use as custom node type
                node_type = node_type_str
            
            # Create node configuration
            config = NodeConfiguration(
                id=node_id,
                type=node_type_str,
                data=node_data
            )
            
            # Create node
            node = self.create_node(
                node_type=node_type,
                node_id=node_id,
                config=config,
                execution_mode=default_execution_mode
            )
            
            nodes[node_id] = node
        
        return nodes
    
    def get_available_node_types(self) -> List[Union[NodeType, str]]:
        """Get list of available node types."""
        types = list(self._node_registry.keys())
        types.extend(self._config.custom_node_registry.keys())
        return types
    
    def is_node_type_supported(self, node_type: Union[NodeType, str]) -> bool:
        """Check if a node type is supported."""
        if isinstance(node_type, NodeType):
            return node_type in self._node_registry
        elif isinstance(node_type, str):
            return (node_type in self._config.custom_node_registry or 
                    any(node_type == str(t) for t in self._node_registry.keys()))
        return False
    
    def get_node_info(self, node_type: Union[NodeType, str]) -> Dict[str, Any]:
        """Get information about a node type."""
        node_class = self._get_node_class(node_type)
        
        # Get constructor signature
        sig = inspect.signature(node_class.__init__)
        
        return {
            "type": str(node_type),
            "class": node_class.__name__,
            "module": node_class.__module__,
            "constructor_params": list(sig.parameters.keys()),
            "docstring": node_class.__doc__,
            "is_abstract": inspect.isabstract(node_class),
        }
    
    def get_factory_metrics(self) -> Dict[str, Any]:
        """Get factory performance metrics."""
        metrics = self._metrics.copy()
        
        if self._node_cache is not None:
            metrics["cache_size"] = len(self._node_cache)
            cache_total = metrics["cache_hits"] + metrics["cache_misses"]
            metrics["cache_hit_rate"] = (
                metrics["cache_hits"] / cache_total * 100 if cache_total > 0 else 0
            )
        
        return metrics
    
    def clear_cache(self) -> None:
        """Clear the node cache."""
        if self._node_cache is not None:
            self._node_cache.clear()
    
    def preload_common_nodes(self) -> None:
        """Preload common node configurations for better performance."""
        common_configs = [
            {
                "id": "input_default",
                "type": NodeType.INPUT,
                "data": {"placeholder": "Enter input..."}
            },
            {
                "id": "output_default", 
                "type": NodeType.OUTPUT,
                "data": {"output_type": "text"}
            },
            {
                "id": "llm_default",
                "type": NodeType.LLM,
                "data": {"model": "gpt-3.5-turbo", "temperature": 0.7}
            },
        ]
        
        for config in common_configs:
            try:
                node_config = NodeConfiguration(
                    id=config["id"],
                    type=str(config["type"]),
                    data=config["data"]
                )
                
                self.create_node(
                    node_type=config["type"],
                    node_id=config["id"],
                    config=node_config
                )
            except Exception:
                # Ignore preloading errors
                pass
    
    def validate_node_config(self, node_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate node configuration.
        
        Args:
            node_config: Node configuration dictionary
            
        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["id", "type"]
        for field in required_fields:
            if field not in node_config:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Check node type
        node_type = node_config["type"]
        if not self.is_node_type_supported(node_type):
            errors.append(f"Unsupported node type: {node_type}")
        
        # Validate node ID format
        node_id = node_config["id"]
        if not isinstance(node_id, str) or not node_id.strip():
            errors.append("Node ID must be a non-empty string")
        
        # Check for reserved characters
        reserved_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"]
        if any(char in node_id for char in reserved_chars):
            warnings.append(f"Node ID contains reserved characters: {reserved_chars}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Global factory instance
_default_factory = None


def get_default_factory() -> NodeFactory:
    """Get the default node factory instance."""
    global _default_factory
    if _default_factory is None:
        _default_factory = NodeFactory()
    return _default_factory


def create_node(
    node_type: Union[NodeType, str],
    node_id: str,
    config: NodeConfiguration,
    execution_mode: Optional[ExecutionMode] = None,
    factory: Optional[NodeFactory] = None
) -> BaseNode:
    """
    Convenience function to create a node using the default factory.
    
    Args:
        node_type: Type of node to create
        node_id: Unique identifier for the node
        config: Node configuration
        execution_mode: Execution mode
        factory: Custom factory instance (uses default if None)
        
    Returns:
        Node instance
    """
    if factory is None:
        factory = get_default_factory()
    
    return factory.create_node(node_type, node_id, config, execution_mode)