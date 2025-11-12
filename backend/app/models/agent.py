"""
Agent model.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from uuid import uuid4


class Agent(Base):
    """Agent model for AI workflows."""
    
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()), index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    graph_json = Column(JSON, nullable=True)  # Stores the node graph configuration
    version = Column(String, default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="agents")
    creator = relationship("User", back_populates="agents")
    runs = relationship("Run", back_populates="agent")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary."""
        return {
            "id": str(self.id),
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "graph_json": self.graph_json,
            "version": self.version,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }