"""
Execution Domain Models

This module contains the core domain entities for the execution system.
All models follow enterprise-grade patterns with comprehensive typing,
validation, and business logic enforcement.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Set, TypedDict, TypeVar, Generic
from uuid import UUID, uuid4
import json
import re

from pydantic import BaseModel, Field, validator, ValidationError


class ExecutionStatus(str, Enum):
    """Execution status enumeration following enterprise standards."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Priority(str, Enum):
    """Execution priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ResourceRequirement:
    """Resource requirements for execution."""
    cpu_cores: int
    memory_mb: int
    gpu_required: bool = False
    max_execution_time: int = 300  # seconds
    network_access: bool = False
    
    def __post_init__(self):
        """Validate resource requirements."""
        if self.cpu_cores <= 0:
            raise ValueError("CPU cores must be positive")
        if self.memory_mb <= 0:
            raise ValueError("Memory must be positive")
        if self.max_execution_time <= 0:
            raise ValueError("Max execution time must be positive")


@dataclass(frozen=True)
class NodeConfiguration:
    """Configuration for individual nodes."""
    node_id: str
    node_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: ResourceRequirement = field(
        default_factory=lambda: ResourceRequirement(1, 512)
    )
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Validate node configuration."""
        if not self.node_id or not self.node_id.strip():
            raise ValueError("Node ID is required")
        if not self.node_type or not self.node_type.strip():
            raise ValueError("Node type is required")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("Retry delay must be non-negative")


@dataclass
class NodeOutput:
    """Output from node execution."""
    node_id: str
    status: NodeStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate node output."""
        if not self.node_id or not self.node_id.strip():
            raise ValueError("Node ID is required")
        if self.execution_time < 0:
            raise ValueError("Execution time must be non-negative")
        if self.tokens_used < 0:
            raise ValueError("Tokens used must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ExecutionEvent:
    """Event emitted during execution."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "execution_started"  # Use string instead of EventType enum
    execution_id: str = ""
    node_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate execution event."""
        if not self.execution_id or not self.execution_id.strip():
            raise ValueError("Execution ID is required")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "execution_id": self.execution_id,
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionMetrics:
    """Metrics collected during execution."""
    total_nodes: int = 0
    completed_nodes: int = 0
    failed_nodes: int = 0
    skipped_nodes: int = 0
    total_execution_time: float = 0.0
    total_tokens_used: int = 0
    peak_memory_usage: int = 0
    peak_cpu_usage: float = 0.0
    network_requests: int = 0
    
    def __post_init__(self):
        """Validate execution metrics."""
        if self.total_nodes < 0:
            raise ValueError("Total nodes must be non-negative")
        if self.completed_nodes < 0:
            raise ValueError("Completed nodes must be non-negative")
        if self.failed_nodes < 0:
            raise ValueError("Failed nodes must be non-negative")
        if self.skipped_nodes < 0:
            raise ValueError("Skipped nodes must be non-negative")
        if self.total_execution_time < 0:
            raise ValueError("Total execution time must be non-negative")
        if self.total_tokens_used < 0:
            raise ValueError("Total tokens used must be non-negative")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_nodes == 0:
            return 0.0
        return (self.completed_nodes / self.total_nodes) * 100
    
    @property
    def average_execution_time(self) -> float:
        """Calculate average execution time per node."""
        if self.completed_nodes == 0:
            return 0.0
        return self.total_execution_time / self.completed_nodes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_nodes": self.total_nodes,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "skipped_nodes": self.skipped_nodes,
            "total_execution_time": self.total_execution_time,
            "total_tokens_used": self.total_tokens_used,
            "peak_memory_usage": self.peak_memory_usage,
            "peak_cpu_usage": self.peak_cpu_usage,
            "network_requests": self.network_requests,
            "success_rate": self.success_rate,
            "average_execution_time": self.average_execution_time,
        }


class ExecutionInput(BaseModel):
    """Input data for execution with validation."""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('inputs')
    def validate_inputs(cls, v):
        """Validate input data."""
        if not isinstance(v, dict):
            raise ValueError("Inputs must be a dictionary")
        return v
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context data."""
        if not isinstance(v, dict):
            raise ValueError("Context must be a dictionary")
        return v


class ExecutionConfig(BaseModel):
    """Configuration for execution with validation."""
    max_execution_time: int = Field(default=300, ge=1, le=3600)
    max_concurrent_nodes: int = Field(default=5, ge=1, le=20)
    enable_streaming: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    retry_failed_nodes: bool = Field(default=True)
    save_intermediate_results: bool = Field(default=True)
    priority: Priority = Field(default=Priority.NORMAL)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


@dataclass
class Execution:
    """Main execution entity representing a graph execution."""
    agent_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: ExecutionStatus = ExecutionStatus.PENDING
    input_data: ExecutionInput = field(default_factory=ExecutionInput)
    config: ExecutionConfig = field(default_factory=ExecutionConfig)
    node_configurations: List[NodeConfiguration] = field(default_factory=list)
    node_outputs: Dict[str, NodeOutput] = field(default_factory=dict)
    events: List[ExecutionEvent] = field(default_factory=list)
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validate execution entity."""
        if not self.agent_id or not self.agent_id.strip():
            raise ValueError("Agent ID is required")
        
        # Validate node configurations
        node_ids = set()
        for node_config in self.node_configurations:
            if node_config.node_id in node_ids:
                raise ValueError(f"Duplicate node ID: {node_config.node_id}")
            node_ids.add(node_config.node_id)
    
    @property
    def is_finished(self) -> bool:
        """Check if execution is finished."""
        return self.status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
        }
    
    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status == ExecutionStatus.RUNNING
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate execution duration in seconds."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def add_event(self, event: ExecutionEvent) -> None:
        """Add an event to the execution."""
        self.events.append(event)
    
    def get_node_output(self, node_id: str) -> Optional[NodeOutput]:
        """Get output for a specific node."""
        return self.node_outputs.get(node_id)
    
    def set_node_output(self, node_output: NodeOutput) -> None:
        """Set output for a specific node."""
        self.node_outputs[node_output.node_id] = node_output
    
    def update_metrics(self) -> None:
        """Update execution metrics based on current state."""
        self.metrics.total_nodes = len(self.node_configurations)
        self.metrics.completed_nodes = sum(
            1 for output in self.node_outputs.values()
            if output.status == NodeStatus.COMPLETED
        )
        self.metrics.failed_nodes = sum(
            1 for output in self.node_outputs.values()
            if output.status == NodeStatus.FAILED
        )
        self.metrics.skipped_nodes = sum(
            1 for output in self.node_outputs.values()
            if output.status == NodeStatus.SKIPPED
        )
        self.metrics.total_tokens_used = sum(
            output.tokens_used for output in self.node_outputs.values()
        )
        self.metrics.total_execution_time = sum(
            output.execution_time for output in self.node_outputs.values()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "input_data": self.input_data.dict(),
            "config": self.config.dict(),
            "node_configurations": [
                {
                    "node_id": nc.node_id,
                    "node_type": nc.node_type,
                    "config": nc.config,
                    "resource_requirements": {
                        "cpu_cores": nc.resource_requirements.cpu_cores,
                        "memory_mb": nc.resource_requirements.memory_mb,
                        "gpu_required": nc.resource_requirements.gpu_required,
                        "max_execution_time": nc.resource_requirements.max_execution_time,
                        "network_access": nc.resource_requirements.network_access,
                    },
                    "timeout": nc.timeout,
                    "retry_count": nc.retry_count,
                    "retry_delay": nc.retry_delay,
                }
                for nc in self.node_configurations
            ],
            "node_outputs": {
                node_id: output.to_dict()
                for node_id, output in self.node_outputs.items()
            },
            "events": [event.to_dict() for event in self.events],
            "metrics": self.metrics.to_dict(),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "duration": self.duration,
            "is_finished": self.is_finished,
            "is_running": self.is_running,
        }


# Type variables for generic interfaces
T = TypeVar('T')
RepositoryType = TypeVar('RepositoryType', bound='Repository')
ServiceType = TypeVar('ServiceType', bound='Service')


class Repository(ABC, Generic[T]):
    """Abstract base class for repositories following DDD patterns."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    async def find_all(self, **filters) -> List[T]:
        """Find all entities matching filters."""
        pass


class Service(ABC):
    """Abstract base class for services following clean architecture."""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute service operation."""
        pass


# Domain events for event sourcing
@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for domain events."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
        }


@dataclass(frozen=True)
class ExecutionStarted(DomainEvent):
    """Event raised when execution starts."""
    execution_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **super().to_dict(),
            "execution_id": self.execution_id,
        }


@dataclass(frozen=True)
class ExecutionCompleted(DomainEvent):
    """Event raised when execution completes."""
    execution_id: str = ""
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **super().to_dict(),
            "execution_id": self.execution_id,
            "metrics": self.metrics.to_dict(),
        }


@dataclass(frozen=True)
class NodeExecutionCompleted(DomainEvent):
    """Event raised when a node completes execution."""
    execution_id: str = ""
    node_id: str = ""
    output: NodeOutput = field(default_factory=lambda: NodeOutput(node_id="unknown", status=NodeStatus.COMPLETED))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **super().to_dict(),
            "execution_id": self.execution_id,
            "node_id": self.node_id,
            "output": self.output.to_dict(),
        }


class EventType(str, Enum):
    """Event type enumeration for execution events."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    EXECUTION_PAUSED = "execution_paused"
    EXECUTION_RESUMED = "execution_resumed"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    TOKEN_STREAM = "token_stream"
    ERROR_OCCURRED = "error_occurred"
    RESOURCE_ALLOCATED = "resource_allocated"
    RESOURCE_RELEASED = "resource_released"


class NodeStatus(str, Enum):
    """Node status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class NodeType(str, Enum):
    """Node type enumeration."""
    INPUT = "input"
    LLM = "llm"
    RETRIEVAL = "retrieval"
    OUTPUT = "output"
    TOOL = "tool"


@dataclass(frozen=True)
class CompiledNode:
    """Compiled node ready for execution."""
    id: str
    type: NodeType
    config: NodeConfiguration
    dependencies: List[str]
    execution_order: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "config": self.config.__dict__ if hasattr(self.config, '__dict__') else self.config,
            "dependencies": self.dependencies,
            "execution_order": self.execution_order,
            "metadata": self.metadata,
        }