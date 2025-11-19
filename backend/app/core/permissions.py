"""
Workspace permission utilities and role-based access control.
"""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace, Membership, MembershipRole


class WorkspacePermission:
    """Workspace permission checker."""
    
    @staticmethod
    def get_user_role(db: Session, user_id: str, workspace_id: str) -> Optional[MembershipRole]:
        """
        Get the role of a user in a workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            MembershipRole or None if user is not a member
        """
        membership = db.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.workspace_id == workspace_id
        ).first()
        
        return membership.role if membership else None
    
    @staticmethod
    def is_member(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user is a member of the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user is a member, False otherwise
        """
        return WorkspacePermission.get_user_role(db, user_id, workspace_id) is not None
    
    @staticmethod
    def is_owner(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user is the owner of the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user is the owner, False otherwise
        """
        return WorkspacePermission.get_user_role(db, user_id, workspace_id) == MembershipRole.OWNER
    
    @staticmethod
    def is_admin(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user is an admin of the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user is an admin or owner, False otherwise
        """
        role = WorkspacePermission.get_user_role(db, user_id, workspace_id)
        return role in [MembershipRole.OWNER, MembershipRole.ADMIN]
    
    @staticmethod
    def can_read(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user can read the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user can read, False otherwise
        """
        return WorkspacePermission.is_member(db, user_id, workspace_id)
    
    @staticmethod
    def can_write(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user can write to the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user can write, False otherwise
        """
        return WorkspacePermission.is_member(db, user_id, workspace_id)
    
    @staticmethod
    def can_delete(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user can delete the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user can delete, False otherwise
        """
        return WorkspacePermission.is_owner(db, user_id, workspace_id)
    
    @staticmethod
    def can_manage_members(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user can manage workspace members.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user can manage members, False otherwise
        """
        return WorkspacePermission.is_admin(db, user_id, workspace_id)
    
    @staticmethod
    def can_manage_agents(db: Session, user_id: str, workspace_id: str) -> bool:
        """
        Check if user can manage agents in the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            True if user can manage agents, False otherwise
        """
        return WorkspacePermission.is_member(db, user_id, workspace_id)
    
    @staticmethod
    def require_membership(db: Session, user_id: str, workspace_id: str) -> Membership:
        """
        Require user to be a member of the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            Membership object
            
        Raises:
            HTTPException: If user is not a member
        """
        membership = db.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.workspace_id == workspace_id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or access denied"
            )
        
        return membership
    
    @staticmethod
    def require_ownership(db: Session, user_id: str, workspace_id: str) -> Membership:
        """
        Require user to be the owner of the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            Membership object
            
        Raises:
            HTTPException: If user is not the owner
        """
        membership = WorkspacePermission.require_membership(db, user_id, workspace_id)
        
        if membership.role != MembershipRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners can perform this action"
            )
        
        return membership
    
    @staticmethod
    def require_admin(db: Session, user_id: str, workspace_id: str) -> Membership:
        """
        Require user to be an admin or owner of the workspace.
        
        Args:
            db: Database session
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            Membership object
            
        Raises:
            HTTPException: If user is not an admin or owner
        """
        membership = WorkspacePermission.require_membership(db, user_id, workspace_id)
        
        if membership.role not in [MembershipRole.OWNER, MembershipRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace admins can perform this action"
            )
        
        return membership


def get_user_workspaces(db: Session, user_id: str) -> list[Workspace]:
    """
    Get all workspaces that a user is a member of.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of workspaces
    """
    workspaces = db.query(Workspace).join(Membership).filter(
        Membership.user_id == user_id
    ).all()
    
    return workspaces


def create_workspace_membership(
    db: Session, 
    user_id: str, 
    workspace_id: str, 
    role: MembershipRole = MembershipRole.MEMBER
) -> Membership:
    """
    Create a workspace membership.
    
    Args:
        db: Database session
        user_id: User ID
        workspace_id: Workspace ID
        role: Membership role
        
    Returns:
        Created membership object
        
    Raises:
        HTTPException: If membership already exists
    """
    # Check if membership already exists
    existing_membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.workspace_id == workspace_id
    ).first()
    
    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace"
        )
    
    # Create new membership
    membership = Membership(
        user_id=user_id,
        workspace_id=workspace_id,
        role=role
    )
    
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    return membership


def remove_workspace_membership(db: Session, user_id: str, workspace_id: str) -> bool:
    """
    Remove a workspace membership.
    
    Args:
        db: Database session
        user_id: User ID
        workspace_id: Workspace ID
        
    Returns:
        True if membership was removed, False if not found
        
    Raises:
        HTTPException: If trying to remove the owner
    """
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.workspace_id == workspace_id
    ).first()
    
    if not membership:
        return False
    
    # Prevent removing the owner
    if membership.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove workspace owner"
        )
    
    db.delete(membership)
    db.commit()
    
    return True


def update_workspace_membership_role(
    db: Session, 
    user_id: str, 
    workspace_id: str, 
    new_role: MembershipRole
) -> Membership:
    """
    Update a workspace membership role.
    
    Args:
        db: Database session
        user_id: User ID
        workspace_id: Workspace ID
        new_role: New membership role
        
    Returns:
        Updated membership object
        
    Raises:
        HTTPException: If membership not found or invalid role change
    """
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.workspace_id == workspace_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    # Prevent changing the owner role
    if membership.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner role"
        )
    
    membership.role = new_role
    db.commit()
    db.refresh(membership)
    
    return membership


# Decorator for requiring permissions
def require_permission(permission: str):
    """
    Decorator for requiring specific permissions.
    
    Args:
        permission: Permission string (e.g., "read", "write", "admin", "owner")
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This is a simplified implementation
            # In a real implementation, you would check the user's permissions
            # against the required permission
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Decorator for requiring workspace membership
def require_workspace_membership(func):
    """
    Decorator for requiring workspace membership.
    
    Returns:
        Decorator function
    """
    def wrapper(*args, **kwargs):
        # This is a simplified implementation
        # In a real implementation, you would check if the user is a member
        return func(*args, **kwargs)
    return wrapper


# Decorator for requiring workspace ownership
def require_workspace_owner(func):
    """
    Decorator for requiring workspace ownership.
    
    Returns:
        Decorator function
    """
    def wrapper(*args, **kwargs):
        # This is a simplified implementation
        # In a real implementation, you would check if the user is the owner
        return func(*args, **kwargs)
    return wrapper


# Decorator for requiring admin permissions
def require_admin(func):
    """
    Decorator for requiring admin permissions.
    
    Returns:
        Decorator function
    """
    def wrapper(*args, **kwargs):
        # This is a simplified implementation
        # In a real implementation, you would check if the user has admin role
        return func(*args, **kwargs)
    return wrapper


def require_workspace_permission(permission: str):
    """
    Decorator for requiring specific workspace permissions.
    
    Args:
        permission: Permission string (e.g., "read", "write", "admin", "owner")
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This is a simplified implementation
            # In a real implementation, you would check the user's permissions
            # against the required permission
            return func(*args, **kwargs)
        return wrapper
    return decorator