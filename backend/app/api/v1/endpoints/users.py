"""
User management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


class UserProfile(BaseModel):
    """User profile model."""
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: str


class UserUpdateRequest(BaseModel):
    """User update request model."""
    full_name: str
    email: EmailStr
    
    @validator("full_name")
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v.strip()
    
    @validator("email")
    def validate_email(cls, v):
        return v.lower()


class UserUpdateResponse(BaseModel):
    """User update response model."""
    message: str
    user: UserProfile


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile.
    """
    logger.info("Get current user profile", user_id=str(current_user.id))
    
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )


@router.put("/me", response_model=UserUpdateResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    """
    logger.info("Update current user profile", user_id=str(current_user.id))
    
    # Check if email is being changed and if it's already taken
    if user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user
    current_user.full_name = user_update.full_name
    current_user.email = user_update.email
    
    db.commit()
    db.refresh(current_user)
    
    return UserUpdateResponse(
        message="Profile updated successfully",
        user=UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None
        )
    )