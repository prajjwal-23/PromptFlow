
"""
Agent management endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
import json

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.permissions import WorkspacePermission
from app.models.user import User
from app.models.workspace import Workspace, Membership
from app.models.agent import Agent
from uuid import uuid4

logger = get_logger(__name__)
router = APIRouter()


# Pydantic Models
class AgentBase(BaseModel):
    """Base agent model."""
    name: str
    description: Optional[str] = None
    graph_json: Optional[Dict[str, Any]] = None
    
    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Agent name must be at least 2 characters long")
        if len(v.strip()) > 100:
            raise ValueError("Agent name must be less than 100 characters long")
        return v.strip()
    
    @validator("description")
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 1000:
            raise ValueError("Description must be less than 1000 characters long")
        return v.strip() if v is not None else v
    
    @validator("graph_json")
    def validate_graph_json(cls, v):
        if v is not None:
            # Basic graph validation
            if not isinstance(v, dict):
                raise ValueError("graph_json must be a dictionary")
            
            # Check for required graph structure
            if "nodes" not in v or not isinstance(v["nodes"], list):
                raise ValueError("graph_json must contain a 'nodes' array")
            
            if "edges" not in v or not isinstance(v["edges"], list):
                raise ValueError("graph_json must contain an 'edges' array")
            
            # Validate each node
            for node in v["nodes"]:
                if not isinstance(node, dict):
                    raise ValueError("Each node must be a dictionary")
                if "id" not in node or "type" not in node:
                    raise ValueError("Each node must have 'id' and 'type' fields")
        
        return v


class AgentCreate(AgentBase):
    """Agent creation model."""
    workspace_id: str
    
    @validator("workspace_id")
    def validate_workspace_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Workspace ID is required")
        return v.strip()


class AgentUpdate(BaseModel):
    """Agent update model."""
    name: Optional[str] = None
    description: Optional[str] = None
    graph_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError("Agent name must be at least 2 characters long")
            if len(v.strip()) > 100:
                raise ValueError("Agent name must be less than 100 characters long")
            return v.strip()
        return v
    
    @validator("description")
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 1000:
            raise ValueError("Description must be less than 1000 characters long")
        return v.strip() if v is not None else v
    
    @validator("graph_json")
    def validate_graph_json(cls, v):
        if v is not None:
            # Basic graph validation
            if not isinstance(v, dict):
                raise ValueError("graph_json must be a dictionary")
            
            # Check for required graph structure
            if "nodes" not in v or not isinstance(v["nodes"], list):
                raise ValueError("graph_json must contain a 'nodes' array")
            
            if "edges" not in v or not isinstance(v["edges"], list):
                raise ValueError("graph_json must contain an 'edges' array")
            
            # Validate each node
            for node in v["nodes"]:
                if not isinstance(node, dict):
                    raise ValueError("Each node must be a dictionary")
                if "id" not in node or "type" not in node:
                    raise ValueError("Each node must have 'id' and 'type' fields")
        
        return v


class AgentResponse(BaseModel):
    """Agent response model."""
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    graph_json: Optional[Dict[str, Any]]
    version: str
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class AgentDuplicateRequest(BaseModel):
    """Agent duplication request model."""
    name: str
    
    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Agent name must be at least 2 characters long")
        if len(v.strip()) > 100:
            raise ValueError("Agent name must be less than 100 characters long")
        return v.strip()


# Helper Functions
def get_agent_with_permission_check(
    db: Session,
    agent_id: str,
    user_id: str
) -> Agent:
    """
    Get agent with permission checking.
    
    Args:
        db: Database session
        agent_id: Agent ID
        user_id: User ID
        
    Returns:
        Agent object
        
    Raises:
        HTTPException: If agent not found or access denied
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check permissions - user must be member of the agent's workspace
    WorkspacePermission.require_membership(db, user_id, agent.workspace_id)
    
    return agent


# Endpoints
@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's agents.
    """
    logger.info("Get user agents", user_id=str(current_user.id), workspace_id=workspace_id)
    
    # Get user's workspaces
    user_workspaces = db.query(Workspace).join(Membership).filter(
        Membership.user_id == str(current_user.id)
    ).all()
    
    workspace_ids = [str(workspace.id) for workspace in user_workspaces]
    
    # If workspace_id is specified, check if user has access to it
    if workspace_id:
        if workspace_id not in workspace_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace"
            )
        workspace_ids = [workspace_id]
    
    # Get agents from accessible workspaces
    agents = db.query(Agent).filter(Agent.workspace_id.in_(workspace_ids)).all()
    
    return [
        AgentResponse(
            id=str(agent.id),
            workspace_id=str(agent.workspace_id),
            name=agent.name,
            description=agent.description,
            graph_json=agent.graph_json,
            version=agent.version,
            is_active=agent.is_active,
            created_by=str(agent.created_by),
            created_at=agent.created_at.isoformat() if agent.created_at else None,
            updated_at=agent.updated_at.isoformat() if agent.updated_at else None
        )
        for agent in agents
    ]


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new agent.
    """
    logger.info("Create new agent", user_id=str(current_user.id), name=agent_data.name)
    
    # Check workspace access
    WorkspacePermission.require_membership(db, str(current_user.id), agent_data.workspace_id)
    
    # Create agent
    agent = Agent(
        id=str(uuid4()),
        workspace_id=agent_data.workspace_id,
        name=agent_data.name,
        description=agent_data.description,
        graph_json=agent_data.graph_json,
        created_by=str(current_user.id)
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return AgentResponse(
        id=str(agent.id),
        workspace_id=str(agent.workspace_id),
        name=agent.name,
        description=agent.description,
        graph_json=agent.graph_json,
        version=agent.version,
        is_active=agent.is_active,
        created_by=str(agent.created_by),
        created_at=agent.created_at.isoformat() if agent.created_at else None,
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get agent by ID.
    """
    logger.info("Get agent", agent_id=agent_id, user_id=str(current_user.id))
    
    agent = get_agent_with_permission_check(db, agent_id, str(current_user.id))
    
    return AgentResponse(
        id=str(agent.id),
        workspace_id=str(agent.workspace_id),
        name=agent.name,
        description=agent.description,
        graph_json=agent.graph_json,
        version=agent.version,
        is_active=agent.is_active,
        created_by=str(agent.created_by),
        created_at=agent.created_at.isoformat() if agent.created_at else None,
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None
    )


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update agent.
    """
    logger.info("Update agent", agent_id=agent_id, user_id=str(current_user.id))
    
    agent = get_agent_with_permission_check(db, agent_id, str(current_user.id))
    
    # Check if user can manage agents in this workspace
    WorkspacePermission.can_manage_agents(db, str(current_user.id), agent.workspace_id)
    
    # Update agent fields
    if agent_update.name is not None:
        agent.name = agent_update.name
    if agent_update.description is not None:
        agent.description = agent_update.description
    if agent_update.graph_json is not None:
        agent.graph_json = agent_update.graph_json
    if agent_update.is_active is not None:
        agent.is_active = agent_update.is_active
    
    db.commit()
    db.refresh(agent)
    
    return AgentResponse(
        id=str(agent.id),
        workspace_id=str(agent.workspace_id),
        name=agent.name,
        description=agent.description,
        graph_json=agent.graph_json,
        version=agent.version,
        is_active=agent.is_active,
        created_by=str(agent.created_by),
        created_at=agent.created_at.isoformat() if agent.created_at else None,
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete agent.
    """
    logger.info("Delete agent", agent_id=agent_id, user_id=str(current_user.id))
    
    agent = get_agent_with_permission_check(db, agent_id, str(current_user.id))
    
    # Check if user can manage agents in this workspace
    WorkspacePermission.can_manage_agents(db, str(current_user.id), agent.workspace_id)
    
    # Only agent creator or workspace admin can delete
    if agent.created_by != str(current_user.id):
        WorkspacePermission.require_admin(db, str(current_user.id), agent.workspace_id)
    
    # Delete agent (cascade will handle runs, etc.)
    db.delete(agent)
    db.commit()


@router.post("/{agent_id}/duplicate", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_agent(
    agent_id: str,
    duplicate_request: AgentDuplicateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate an agent.
    """
    logger.info("Duplicate agent", agent_id=agent_id, user_id=str(current_user.id))
    
    source_agent = get_agent_with_permission_check(db, agent_id, str(current_user.id))
    
    # Check workspace access
    WorkspacePermission.require_membership(db, str(current_user.id), source_agent.workspace_id)
    
    # Check if agent name already exists in the workspace
    existing_agent = db.query(Agent).filter(
        Agent.workspace_id == source_agent.workspace_id,
        Agent.name == duplicate_request.name
    ).first()
    
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent with this name already exists in the workspace"
        )
    
    # Create duplicated agent
    duplicated_agent = Agent(
        id=str(uuid4()),
        workspace_id=source_agent.workspace_id,
        name=duplicate_request.name,
        description=source_agent.description,
        graph_json=source_agent.graph_json,
        created_by=str(current_user.id)
    )
    
    db.add(duplicated_agent)
    db.commit()
    db.refresh(duplicated_agent)
    
    return AgentResponse(
        id=str(duplicated_agent.id),
        workspace_id=str(duplicated_agent.workspace_id),
        name=duplicated_agent.name,
        description=duplicated_agent.description,
        graph_json=duplicated_agent.graph_json,
        version=duplicated_agent.version,
        is_active=duplicated_agent.is_active,
        created_by=str(duplicated_agent.created_by),
        created_at=duplicated_agent.created_at.isoformat() if duplicated_agent.created_at else None,
        updated_at=duplicated_agent.updated_at.isoformat() if duplicated_agent.updated_at else None
    )
