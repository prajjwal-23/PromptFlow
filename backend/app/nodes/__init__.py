"""
Nodes Module

This module provides the complete node system for the PromptFlow execution engine
including base interfaces, core node types, and factory patterns.
"""

from ..execution.nodes.base_node import (
    BaseNode,
    ProcessingNode,
    NodeInput,
    NodeOutput,
    NodeContext,
    NodeMetrics,
    NodeStatus,
    NodeType,
    ExecutionMode,
)

from .input_node import InputNode
from .output_node import OutputNode
from .llm_node import LLMNode, LLMRequest, LLMResponse
from .retrieval_node import RetrievalNode, RetrievalQuery, RetrievalResult, RetrievalResponse
from .tool_node import ToolNode, ToolRequest, ToolResponse
from .factory import (
    NodeFactory,
    NodeFactoryConfig,
    get_default_factory,
    create_node,
)

# Export all node types
__all__ = [
    # Base classes and interfaces
    "BaseNode",
    "ProcessingNode",
    "NodeInput",
    "NodeOutput",
    "NodeContext",
    "NodeMetrics",
    "NodeStatus",
    "NodeType",
    "ExecutionMode",
    
    # Core node implementations
    "InputNode",
    "OutputNode",
    "LLMNode",
    "RetrievalNode",
    "ToolNode",
    
    # LLM node types
    "LLMRequest",
    "LLMResponse",
    
    # Retrieval node types
    "RetrievalQuery",
    "RetrievalResult",
    "RetrievalResponse",
    
    # Tool node types
    "ToolRequest",
    "ToolResponse",
    
    # Factory and utilities
    "NodeFactory",
    "NodeFactoryConfig",
    "get_default_factory",
    "create_node",
]

# Version info
__version__ = "1.0.0"