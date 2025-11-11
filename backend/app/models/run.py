"""
Run and run event models.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Run(Base):
    """Run model for agent execution tracking."""
    
    __tablename__ = "runs"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    input_data = Column(JSON, nullable=True)  # Input data for the run
    output_data = Column(JSON, nullable=True)  # Output data from the run
    error_message = Column(Text, nullable=True)  # Error message if failed
    metrics = Column(JSON, nullable=True)  # Performance metrics (tokens, duration, etc.)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    agent = relationship("Agent", back_populates="runs")
    creator = relationship("User", back_populates="runs")
    events = relationship("RunEvent", back_populates="run")
    
    def __repr__(self):
        return f"<Run(id={self.id}, agent_id={self.agent_id}, status={self.status})>"


class RunEvent(Base):
    """Run event model for detailed execution logging."""
    
    __tablename__ = "run_events"
    
    id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    node_id = Column(String, nullable=True)  # Node that generated this event
    event_type = Column(String, nullable=False)  # node_start, node_complete, error, log, etc.
    level = Column(String, default="info", nullable=False)  # debug, info, warning, error
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional event data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Metrics specific to this event
    duration_ms = Column(Float, nullable=True)  # Event duration in milliseconds
    token_count = Column(Integer, nullable=True)  # For LLM events
    
    # Relationships
    run = relationship("Run", back_populates="events")
    
    def __repr__(self):
        return f"<RunEvent(id={self.id}, run_id={self.run_id}, event_type={self.event_type})>"