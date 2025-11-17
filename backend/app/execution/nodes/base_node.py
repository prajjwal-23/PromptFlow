"""
Base Node Interface

This module provides the base node interface and abstract implementations
for all node types in the PromptFlow execution engine following enterprise-grade patterns.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Optional, Set, Tuple, Union, AsyncGenerator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
from contextlib import asynccontextmanager

from ...domain.execution.models import ExecutionConfig, NodeConfiguration, DomainEvent, ExecutionStarted, NodeExecutionCompleted


class NodeStatus(str, Enum):
    """Node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class NodeType(str, Enum):
    """Supported node types."""
    INPUT = "input"
    LLM = "llm"
    RETRIEVAL = "retrieval"
    OUTPUT = "output"
    TOOL = "tool"


class ExecutionMode(str, Enum):
    """Node execution modes."""
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"


@dataclass(frozen=True)
class NodeInput:
    """Node input data structure."""
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_nodes: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "data": self.data,
            "metadata": self.metadata,
            "source_nodes": self.source_nodes,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class NodeOutput:
    """Node output data structure."""
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "data": self.data,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


@dataclass(frozen=True)
class NodeContext:
    """Node execution context."""
    node_id: str
    execution_id: str
    workspace_id: str
    user_id: str
    config: ExecutionConfig
    global_state: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, NodeOutput] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "execution_id": self.execution_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config,
            "global_state": self.global_state,
            "dependencies": {k: v.to_dict() for k, v in self.dependencies.items()},
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class NodeMetrics:
    """Node execution metrics."""
    execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    input_size: int = 0
    output_size: int = 0
    error_count: int = 0
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseNode(ABC):
    """Abstract base class for all node types."""
    
    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        """
        Initialize base node.
        
        Args:
            node_id: Unique identifier for the node
            node_type: Type of the node
            config: Node configuration
            execution_mode: Execution mode (sync, async, streaming)
        """
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
        self.execution_mode = execution_mode
        self.status = NodeStatus.PENDING
        self.metrics = NodeMetrics()
        self._execution_context: Optional[NodeContext] = None
        self._event_handlers: List[callable] = []
        self._lock = asyncio.Lock()
    
    @property
    def is_running(self) -> bool:
        """Check if node is currently running."""
        return self.status == NodeStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if node execution is completed."""
        return self.status in [NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.CANCELLED, NodeStatus.SKIPPED]
    
    @property
    def can_execute(self) -> bool:
        """Check if node can be executed."""
        return self.status in [NodeStatus.PENDING, NodeStatus.FAILED]
    
    def add_event_handler(self, handler: callable) -> None:
        """Add event handler for node events."""
        self._event_handlers.append(handler)
    
    def remove_event_handler(self, handler: callable) -> None:
        """Remove event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
    async def _emit_event(self, event: DomainEvent) -> None:
        """Emit event to all registered handlers."""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # Log error but don't fail the execution
                print(f"Error in event handler: {e}")
    
    @asynccontextmanager
    async def execution_context(self, context: NodeContext):
        """Context manager for node execution."""
        async with self._lock:
            self._execution_context = context
            self.status = NodeStatus.RUNNING
            self.metrics = NodeMetrics()
            
            # Emit execution started event
            await self._emit_event(ExecutionStarted(
                execution_id=context.execution_id
            ))
            
            try:
                yield
            except Exception as e:
                self.status = NodeStatus.FAILED
                self.metrics.error_count += 1
                raise
            finally:
                if self.status == NodeStatus.RUNNING:
                    self.status = NodeStatus.COMPLETED
                
                # Emit execution completed event
                await self._emit_event(NodeExecutionCompleted(
                    execution_id=context.execution_id,
                    node_id=self.node_id
                ))
                
                self._execution_context = None
    
    @abstractmethod
    async def validate_input(self, input_data: NodeInput) -> bool:
        """
        Validate input data for the node.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """
        Preprocess input data before execution.
        
        Args:
            input_data: Raw input data
            
        Returns:
            Preprocessed input data
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """
        Execute the node logic.
        
        Args:
            input_data: Processed input data
            context: Execution context
            
        Returns:
            Node execution output
        """
        pass
    
    @abstractmethod
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """
        Postprocess output data after execution.
        
        Args:
            output: Raw output data
            context: Execution context
            
        Returns:
            Postprocessed output data
        """
        pass
    
    async def execute_sync(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """
        Execute node synchronously.
        
        Args:
            input_data: Input data
            context: Execution context
            
        Returns:
            Node execution output
        """
        start_time = datetime.now()
        
        async with self.execution_context(context):
            try:
                # Validate input
                if not await self.validate_input(input_data):
                    raise ValueError("Invalid input data")
                
                # Preprocess input
                processed_input = await self.preprocess_input(input_data)
                
                # Execute node logic
                output = await self.execute(processed_input, context)
                
                # Postprocess output
                final_output = await self.postprocess_output(output, context)
                
                # Update metrics
                execution_time = (datetime.now() - start_time).total_seconds()
                self.metrics = NodeMetrics(
                    execution_time=execution_time,
                    input_size=len(json.dumps(input_data.data).encode('utf-8')),
                    output_size=len(json.dumps(final_output.data).encode('utf-8'))
                )
                
                return final_output
                
            except Exception as e:
                error_output = NodeOutput(
                    data={},
                    error=str(e),
                    timestamp=datetime.now()
                )
                return error_output
    
    async def execute_async(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """
        Execute node asynchronously.
        
        Args:
            input_data: Input data
            context: Execution context
            
        Returns:
            Node execution output
        """
        # For async execution, we run the sync execution in a background task
        return await asyncio.create_task(self.execute_sync(input_data, context))
    
    async def execute_streaming(self, input_data: NodeInput, context: NodeContext) -> AsyncGenerator[NodeOutput, None]:
        """
        Execute node with streaming output.
        
        Args:
            input_data: Input data
            context: Execution context
            
        Yields:
            Partial node outputs
        """
        # Default implementation - just yield the final result
        final_output = await self.execute_sync(input_data, context)
        yield final_output
    
    async def run(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """
        Run node with appropriate execution mode.
        
        Args:
            input_data: Input data
            context: Execution context
            
        Returns:
            Node execution output
        """
        if not self.can_execute:
            raise RuntimeError(f"Node {self.node_id} cannot be executed in current state: {self.status}")
        
        if self.execution_mode == ExecutionMode.SYNC:
            return await self.execute_sync(input_data, context)
        elif self.execution_mode == ExecutionMode.ASYNC:
            return await self.execute_async(input_data, context)
        elif self.execution_mode == ExecutionMode.STREAMING:
            # For streaming mode, collect all chunks and return the last one
            final_output = None
            async for output in self.execute_streaming(input_data, context):
                final_output = output
            return final_output or NodeOutput(data={}, error="No output generated")
        else:
            raise ValueError(f"Unsupported execution mode: {self.execution_mode}")
    
    async def cancel(self) -> None:
        """Cancel node execution."""
        async with self._lock:
            if self.status == NodeStatus.RUNNING:
                self.status = NodeStatus.CANCELLED
    
    async def reset(self) -> None:
        """Reset node to initial state."""
        async with self._lock:
            self.status = NodeStatus.PENDING
            self.metrics = NodeMetrics()
            self._execution_context = None
    
    def get_status(self) -> NodeStatus:
        """Get current node status."""
        return self.status
    
    def get_metrics(self) -> NodeMetrics:
        """Get node execution metrics."""
        return self.metrics
    
    def get_config(self) -> NodeConfiguration:
        """Get node configuration."""
        return self.config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config,
            "execution_mode": self.execution_mode.value,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
        }


class ProcessingNode(BaseNode):
    """Base class for nodes that process data."""
    
    def __init__(
        self,
        node_id: str,
        node_type: NodeType,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ):
        super().__init__(node_id, node_type, config, execution_mode)
        self._processing_rules = self._create_processing_rules()
    
    def _create_processing_rules(self) -> List[str]:
        """Create processing rules for the node."""
        return [
            "input_validation",
            "data_transformation",
            "output_formatting",
            "error_handling",
        ]
    
    async def validate_input(self, input_data: NodeInput) -> bool:
        """Validate input data for processing node."""
        # Basic validation
        if not input_data.data:
            return False
        
        # Check required fields based on node type
        required_fields = self._get_required_fields()
        for field in required_fields:
            if field not in input_data.data:
                return False
        
        return True
    
    @abstractmethod
    def _get_required_fields(self) -> List[str]:
        """Get list of required input fields for this node type."""
        pass
    
    async def preprocess_input(self, input_data: NodeInput) -> NodeInput:
        """Preprocess input data for processing node."""
        # Default preprocessing - just return the input as-is
        return input_data
    
    async def postprocess_output(self, output: NodeOutput, context: NodeContext) -> NodeOutput:
        """Postprocess output data for processing node."""
        # Default postprocessing - add metadata
        enhanced_metadata = output.metadata.copy()
        enhanced_metadata.update({
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "execution_mode": self.execution_mode.value,
            "processed_at": datetime.now().isoformat(),
        })
        
        return NodeOutput(
            data=output.data,
            metadata=enhanced_metadata,
            timestamp=output.timestamp,
            error=output.error
        )


class InputNode(ProcessingNode):
    """Input node for receiving external data."""
    
    def __init__(self, node_id: str, config: NodeConfiguration):
        super().__init__(node_id, NodeType.INPUT, config)
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for input node."""
        return ["value"]
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute input node."""
        # Input node simply passes through the input data
        return NodeOutput(
            data=input_data.data,
            metadata={"node_type": "input", "processed": True}
        )


class OutputNode(ProcessingNode):
    """Output node for final data output."""
    
    def __init__(self, node_id: str, config: NodeConfiguration):
        super().__init__(node_id, NodeType.OUTPUT, config)
    
    def _get_required_fields(self) -> List[str]:
        """Get required fields for output node."""
        return ["result"]
    
    async def execute(self, input_data: NodeInput, context: NodeContext) -> NodeOutput:
        """Execute output node."""
        # Output node formats the final result
        output_type = self.config.config.get("output_type", "text")
        
        formatted_data = self._format_output(input_data.data, output_type)
        
        return NodeOutput(
            data={"result": formatted_data, "type": output_type},
            metadata={"node_type": "output", "formatted": True}
        )
    
    def _format_output(self, data: Dict[str, Any], output_type: str) -> Union[str, Dict[str, Any]]:
        """Format output data based on output type."""
        if output_type == "json":
            return json.dumps(data, indent=2)
        elif output_type == "text":
            return str(data)
        elif output_type == "markdown":
            return self._to_markdown(data)
        elif output_type == "html":
            return self._to_html(data)
        else:
            return data
    
    def _to_markdown(self, data: Dict[str, Any]) -> str:
        """Convert data to markdown format."""
        lines = ["# Output Result"]
        for key, value in data.items():
            lines.append(f"## {key}")
            lines.append(f"```\n{value}\n```")
        return "\n".join(lines)
    
    def _to_html(self, data: Dict[str, Any]) -> str:
        """Convert data to HTML format."""
        lines = ["<div class='output-result'>"]
        lines.append("<h1>Output Result</h1>")
        for key, value in data.items():
            lines.append(f"<h2>{key}</h2>")
            lines.append(f"<pre>{value}</pre>")
        lines.append("</div>")
        return "\n".join(lines)


class NodeFactory:
    """Factory for creating node instances."""
    
    _node_registry = {
        NodeType.INPUT: InputNode,
        NodeType.OUTPUT: OutputNode,
    }
    
    @classmethod
    def register_node_type(cls, node_type: NodeType, node_class: type) -> None:
        """Register a new node type."""
        cls._node_registry[node_type] = node_class
    
    @classmethod
    def create_node(
        self,
        node_type: NodeType,
        node_id: str,
        config: NodeConfiguration,
        execution_mode: ExecutionMode = ExecutionMode.SYNC
    ) -> BaseNode:
        """
        Create a node instance.
        
        Args:
            node_type: Type of node to create
            node_id: Unique identifier for the node
            config: Node configuration
            execution_mode: Execution mode
            
        Returns:
            Node instance
        """
        if node_type not in self._node_registry:
            raise ValueError(f"Unknown node type: {node_type}")
        
        node_class = self._node_registry[node_type]
        return node_class(node_id, config, execution_mode)
    
    @classmethod
    def get_available_node_types(cls) -> List[NodeType]:
        """Get list of available node types."""
        return list(cls._node_registry.keys())
    
    @classmethod
    def is_node_type_supported(cls, node_type: NodeType) -> bool:
        """Check if a node type is supported."""
        return node_type in cls._node_registry