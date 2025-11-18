"""
Run and run event models.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional

from app.core.database import Base


class Run(Base):
    """Run model for agent execution tracking."""
    
    __tablename__ = "runs"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed, cancelled, paused
    input_data = Column(JSON, nullable=True)  # Input data for the run
    output_data = Column(JSON, nullable=True)  # Output data from the run
    error_message = Column(Text, nullable=True)  # Error message if failed
    metrics = Column(JSON, nullable=True)  # Performance metrics (tokens, duration, etc.)
    
    # Timing fields
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Execution configuration
    config = Column(JSON, nullable=True)  # Execution configuration
    priority = Column(String, default="normal", nullable=False)  # low, normal, high, urgent
    timeout_seconds = Column(Integer, default=3600, nullable=False)  # Execution timeout in seconds
    max_retries = Column(Integer, default=3, nullable=False)  # Maximum retry attempts
    memory_limit_mb = Column(Integer, default=1024, nullable=False)  # Memory limit in MB
    max_parallel_nodes = Column(Integer, default=5, nullable=False)  # Maximum parallel nodes
    
    # Progress tracking
    total_nodes = Column(Integer, default=0, nullable=False)  # Total number of nodes
    completed_nodes = Column(Integer, default=0, nullable=False)  # Completed nodes count
    failed_nodes = Column(Integer, default=0, nullable=False)  # Failed nodes count
    skipped_nodes = Column(Integer, default=0, nullable=False)  # Skipped nodes count
    
    # Resource usage
    peak_memory_usage = Column(Integer, nullable=True)  # Peak memory usage in MB
    total_tokens_used = Column(Integer, default=0, nullable=False)  # Total tokens used
    total_execution_time = Column(Float, default=0.0, nullable=False)  # Total execution time in seconds
    
    # Metadata
    run_metadata = Column(JSON, nullable=True)  # Additional metadata
    tags = Column(JSON, nullable=True)  # Tags for categorization
    parent_run_id = Column(String, ForeignKey("runs.id"), nullable=True)  # For chained executions
    
    # Relationships
    agent = relationship("Agent", back_populates="runs")
    creator = relationship("User", back_populates="runs")
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    child_runs = relationship("Run", remote_side=[parent_run_id], back_populates="parent_run")
    
    def __repr__(self):
        return f"<Run(id={self.id}, agent_id={self.agent_id}, status={self.status})>"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if run is finished."""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def is_running(self) -> bool:
        """Check if run is currently running."""
        return self.status == "running"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of nodes."""
        if self.total_nodes == 0:
            return 0.0
        return (self.completed_nodes / self.total_nodes) * 100


class RunEvent(Base):
    """Run event model for detailed execution logging."""
    
    __tablename__ = "run_events"
    
    id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False, index=True)
    node_id = Column(String, nullable=True, index=True)  # Node that generated this event
    event_type = Column(String, nullable=False, index=True)  # node_start, node_complete, error, log, etc.
    level = Column(String, default="info", nullable=False, index=True)  # debug, info, warning, error
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional event data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Metrics specific to this event
    duration_ms = Column(Float, nullable=True)  # Event duration in milliseconds
    token_count = Column(Integer, nullable=True)  # For LLM events
    memory_usage_mb = Column(Float, nullable=True)  # Memory usage at time of event
    cpu_usage_percent = Column(Float, nullable=True)  # CPU usage at time of event
    
    # Error details
    error_type = Column(String, nullable=True)  # Type of error if any
    stack_trace = Column(Text, nullable=True)  # Stack trace for debugging
    
    # Execution context
    execution_context = Column(JSON, nullable=True)  # Execution context information
    node_config = Column(JSON, nullable=True)  # Node configuration at time of event
    
    # Resource tracking
    resource_id = Column(String, nullable=True)  # Resource identifier
    resource_type = Column(String, nullable=True)  # Type of resource (llm, tool, etc.)
    
    # Relationships
    run = relationship("Run", back_populates="events", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RunEvent(id={self.id}, run_id={self.run_id}, event_type={self.event_type}, level={self.level})>"