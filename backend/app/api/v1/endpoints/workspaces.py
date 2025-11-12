"""
Workspace management endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permissions import (
    WorkspacePermission,
    get_user_workspaces,
    create_workspace_membership,
    remove_workspace_membership,
    update_workspace_membership_role
)
from app.models.user import User
from app.models.workspace import Workspace, Membership, MembershipRole
from app.models.user import User
from uuid import uuid4

logger = get_logger(__name__)
router = APIRouter()


# Pydantic Models
class WorkspaceBase(BaseModel):
    """Base workspace model."""
    name: str
    description: Optional[str] = None
    
    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Workspace name must be at least 2 characters long")
        if len(v.strip()) > 100:
            raise ValueError("Workspace name must be less than 100 characters long")
        return v.strip()


class WorkspaceCreate(WorkspaceBase):
    """Workspace creation model."""
    pass


class WorkspaceUpdate(BaseModel):
    """Workspace update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    
    @validator("name")
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Workspace name must be at least 2 characters long")
        if v is not None and len(v.strip()) > 100:
            raise ValueError("Workspace name must be less than 100 characters long")
        return v.strip() if v is not None else v


class WorkspaceResponse(BaseModel):
    """Workspace response model."""
    id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    role: str
    member_count: int
    
    class Config:
        from_attributes = True


class WorkspaceMember(BaseModel):
    """Workspace member model."""
    id: str
    user_id: str
    email: str
    full_name: str
    role: str
    created_at: str
    
    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    """Member creation model."""
    email: str
    role: MembershipRole = MembershipRole.MEMBER
    
    @validator("email")
    def validate_email(cls, v):
        if not v or "@" not in v:
            raise ValueError("Valid email is required")
        return v.lower()


class MemberUpdate(BaseModel):
    """Member update model."""
    role: MembershipRole


# Helper Functions
def get_workspace_with_permission_check(
    db: Session,
    workspace_id: str,
    user_id: str,
    require_admin: bool = False
) -> Workspace:
    """
    Get workspace with permission checking.
    
    Args:
        db: Database session
        workspace_id: Workspace ID
        user_id: User ID
        require_admin: Whether to require admin permissions
        
    Returns:
        Workspace object
        
    Raises:
        HTTPException: If workspace not found or access denied
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check permissions
    if require_admin:
        WorkspacePermission.require_admin(db, user_id, workspace_id)
    else:
        WorkspacePermission.require_membership(db, user_id, workspace_id)
    
    return workspace


# Endpoints
@router.get("/", response_model=List[WorkspaceResponse])
async def get_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's workspaces.
    """
    logger.info("Get user workspaces", user_id=str(current_user.id))
    
    workspaces = get_user_workspaces(db, str(current_user.id))
    
    return [
        WorkspaceResponse(
            id=str(workspace.id),
            name=workspace.name,
            description=workspace.description,
            created_by=workspace.created_by,
            created_at=workspace.created_at.isoformat() if workspace.created_at else None,
            updated_at=workspace.updated_at.isoformat() if workspace.updated_at else None,
            role=workspace.get_user_role(str(current_user.id)) or "member",
            member_count=len(workspace.memberships)
        )
        for workspace in workspaces
    ]


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new workspace.
    """
    logger.info("Create new workspace", user_id=str(current_user.id), name=workspace_data.name)
    
    # Create workspace
    workspace = Workspace(
        id=str(uuid4()),
        name=workspace_data.name,
        description=workspace_data.description,
        created_by=str(current_user.id)
    )
    
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    # Create owner membership
    create_workspace_membership(
        db, 
        str(current_user.id), 
        str(workspace.id), 
        MembershipRole.OWNER
    )
    
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        description=workspace.description,
        created_by=workspace.created_by,
        created_at=workspace.created_at.isoformat() if workspace.created_at else None,
        updated_at=workspace.updated_at.isoformat() if workspace.updated_at else None,
        role="owner",
        member_count=1
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get workspace by ID.
    """
    logger.info("Get workspace", workspace_id=workspace_id, user_id=str(current_user.id))
    
    workspace = get_workspace_with_permission_check(db, workspace_id, str(current_user.id))
    
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        description=workspace.description,
        created_by=workspace.created_by,
        created_at=workspace.created_at.isoformat() if workspace.created_at else None,
        updated_at=workspace.updated_at.isoformat() if workspace.updated_at else None,
        role=workspace.get_user_role(str(current_user.id)) or "member",
        member_count=len(workspace.memberships)
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    workspace_update: WorkspaceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update workspace.
    """
    logger.info("Update workspace", workspace_id=workspace_id, user_id=str(current_user.id))
    
    workspace = get_workspace_with_permission_check(
        db, workspace_id, str(current_user.id), require_admin=True
    )
    
    # Update workspace fields
    if workspace_update.name is not None:
        workspace.name = workspace_update.name
    if workspace_update.description is not None:
        workspace.description = workspace_update.description
    
    db.commit()
    db.refresh(workspace)
    
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        description=workspace.description,
        created_by=workspace.created_by,
        created_at=workspace.created_at.isoformat() if workspace.created_at else None,
        updated_at=workspace.updated_at.isoformat() if workspace.updated_at else None,
        role=workspace.get_user_role(str(current_user.id)) or "member",
        member_count=len(workspace.memberships)
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete workspace.
    """
    logger.info("Delete workspace", workspace_id=workspace_id, user_id=str(current_user.id))
    
    workspace = get_workspace_with_permission_check(
        db, workspace_id, str(current_user.id), require_admin=False
    )
    
    # Only owners can delete workspaces
    WorkspacePermission.require_ownership(db, str(current_user.id), workspace_id)
    
    # Delete workspace (cascade will handle memberships, agents, etc.)
    db.delete(workspace)
    db.commit()


# Member Management Endpoints
@router.get("/{workspace_id}/members", response_model=List[WorkspaceMember])
async def get_workspace_members(
    workspace_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get workspace members.
    """
    logger.info("Get workspace members", workspace_id=workspace_id, user_id=str(current_user.id))
    
    workspace = get_workspace_with_permission_check(db, workspace_id, str(current_user.id))
    
    members = db.query(Membership).filter(Membership.workspace_id == workspace_id).all()
    
    return [
        WorkspaceMember(
            id=str(membership.id),
            user_id=membership.user_id,
            email=membership.user.email,
            full_name=membership.user.full_name,
            role=membership.role.value,
            created_at=membership.created_at.isoformat() if membership.created_at else None
        )
        for membership in members
    ]


@router.post("/{workspace_id}/members", response_model=WorkspaceMember, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: str,
    member_data: MemberCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a member to the workspace.
    """
    logger.info("Add workspace member", workspace_id=workspace_id, user_id=str(current_user.id))
    
    workspace = get_workspace_with_permission_check(
        db, workspace_id, str(current_user.id), require_admin=True
    )
    
    # Find user to add
    user_to_add = db.query(User).filter(User.email == member_data.email).first()
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found"
        )
    
    # Create membership
    membership = create_workspace_membership(
        db,
        str(user_to_add.id),
        workspace_id,
        member_data.role
    )
    
    return WorkspaceMember(
        id=str(membership.id),
        user_id=membership.user_id,
        email=membership.user.email,
        full_name=membership.user.full_name,
        role=membership.role.value,
        created_at=membership.created_at.isoformat() if membership.created_at else None
    )


@router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMember)
async def update_workspace_member(
    workspace_id: str,
    user_id: str,
    member_update: MemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update workspace member role.
    """
    logger.info("Update workspace member", workspace_id=workspace_id, user_id=user_id)
    
    workspace = get_workspace_with_permission_check(
        db, workspace_id, str(current_user.id), require_admin=True
    )
    
    # Update membership role
    membership = update_workspace_membership_role(
        db,
        user_id,
        workspace_id,
        member_update.role
    )
    
    return WorkspaceMember(
        id=str(membership.id),
        user_id=membership.user_id,
        email=membership.user.email,
        full_name=membership.user.full_name,
        role=membership.role.value,
        created_at=membership.created_at.isoformat() if membership.created_at else None
    )


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from the workspace.
    """
    logger.info("Remove workspace member", workspace_id=workspace_id, user_id=user_id)
    
    workspace = get_workspace_with_permission_check(
        db, workspace_id, str(current_user.id), require_admin=True
    )
    
    # Remove membership
    success = remove_workspace_membership(db, user_id, workspace_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )