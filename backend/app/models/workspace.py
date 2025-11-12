"""
Workspace and membership models.
"""

from uuid import uuid4
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
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
    
    # Primary key using String for consistency
    id = Column(String, primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership and timestamps
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="created_workspaces")
    memberships = relationship("Membership", back_populates="workspace", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="workspace", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name={self.name})>"
    
    def has_member(self, user_id: str) -> bool:
        """Check if a user is a member of this workspace."""
        return any(membership.user_id == user_id for membership in self.memberships)
    
    def get_user_role(self, user_id: str) -> Optional[str]:
        """Get the role of a user in this workspace."""
        for membership in self.memberships:
            if membership.user_id == user_id:
                return membership.role.value
        return None
    
    def to_dict_with_role(self, user_id: str) -> dict:
        """Convert workspace to dictionary with user role included."""
        workspace_dict = self.to_dict()
        workspace_dict["role"] = self.get_user_role(user_id) or "member"
        workspace_dict["member_count"] = len(self.memberships)
        return workspace_dict
    
    def to_dict(self) -> dict:
        """Convert workspace to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Membership(Base):
    """Membership model for user-workspace relationships."""
    
    __tablename__ = "memberships"
    
    # Primary key using String for consistency
    id = Column(String, primary_key=True, default=lambda: str(uuid4()), index=True)
    
    # Foreign keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    
    # Membership details
    role = Column(Enum(MembershipRole), default=MembershipRole.MEMBER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    workspace = relationship("Workspace", back_populates="memberships")
    
    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, workspace_id={self.workspace_id}, role={self.role})>"
    
    def to_dict(self) -> dict:
        """Convert membership to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }