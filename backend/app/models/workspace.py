"""
Workspace and membership models.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
import enum


class MembershipRole(str, enum.Enum):
    """Membership roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Workspace(Base):
    """Workspace model for organizing projects."""
    
    __tablename__ = "workspaces"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="created_workspaces")
    memberships = relationship("Membership", back_populates="workspace")
    agents = relationship("Agent", back_populates="workspace")
    datasets = relationship("Dataset", back_populates="workspace")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name={self.name})>"


class Membership(Base):
    """Membership model for user-workspace relationships."""
    
    __tablename__ = "memberships"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    role = Column(Enum(MembershipRole), default=MembershipRole.MEMBER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="memberships")
    
    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, workspace_id={self.workspace_id}, role={self.role})>"