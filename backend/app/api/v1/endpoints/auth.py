"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from app.core.auth import (
    authenticate_user,
    create_token_pair,
    refresh_access_token,
    get_password_hash,
    get_current_active_user
)
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RegisterRequest(BaseModel):
    """Register request model."""
    email: EmailStr
    password: str
    full_name: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    @validator("full_name")
    def validate_full_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v.strip()
    
    @validator("email")
    def validate_email(cls, v):
        # Additional email validation if needed
        return v.lower()


class RegisterResponse(BaseModel):
    """Register response model."""
    message: str
    user: dict


class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    logger.info("User registration attempt", email=request.email)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    password_hash = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        password_hash=password_hash,  # Use correct field name
        full_name=request.full_name,
        is_active=True
    )
    
    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info("User registered successfully", user_id=str(new_user.id))
    
    return RegisterResponse(
        message="User registered successfully",
        user={
            "id": str(new_user.id),
            "email": new_user.email,
            "full_name": new_user.full_name,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None
        }
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    """
    logger.info("Login attempt", email=request.email)
    
    # Authenticate user
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token pair
    tokens = create_token_pair(user)
    
    logger.info("User logged in successfully", user_id=str(user.id))
    
    return LoginResponse(**tokens)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    logger.info("Token refresh attempt")
    
    try:
        new_token_data = await refresh_access_token(request.refresh_token, db)
        logger.info("Token refreshed successfully")
        return RefreshResponse(**new_token_data)
    except HTTPException:
        logger.warning("Invalid refresh token attempt")
        raise


@router.post("/logout")
async def logout():
    """
    Logout user.
    
    Note: In a stateful JWT implementation, we would add the token to a blacklist.
    For stateless JWT, we rely on token expiration.
    """
    logger.info("Logout attempt")
    
    # In a real implementation, you might:
    # 1. Add token to Redis blacklist
    # 2. Log the logout event
    # 3. Perform any cleanup
    
    return {"message": "Logged out successfully"}


@router.post("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify if the current token is valid.
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email
    }