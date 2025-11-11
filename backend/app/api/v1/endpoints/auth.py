"""
Authentication endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class RegisterRequest(BaseModel):
    """Register request model."""
    email: str
    password: str
    full_name: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return access token.
    
    This is a placeholder implementation for Phase 1.
    """
    logger.info("Login attempt", email=request.email)
    
    # TODO: Implement actual authentication logic
    # For now, return a mock response
    
    return LoginResponse(
        access_token="mock_token_for_phase_1",
        user={
            "id": "1",
            "email": request.email,
            "full_name": "Demo User"
        }
    )


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    This is a placeholder implementation for Phase 1.
    """
    logger.info("Registration attempt", email=request.email)
    
    # TODO: Implement actual user registration logic
    # For now, return a mock response
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": "1",
            "email": request.email,
            "full_name": request.full_name
        }
    }


@router.post("/refresh")
async def refresh_token():
    """
    Refresh access token.
    
    This is a placeholder implementation for Phase 1.
    """
    logger.info("Token refresh attempt")
    
    # TODO: Implement actual token refresh logic
    
    return {
        "access_token": "new_mock_token_for_phase_1",
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout():
    """
    Logout user.
    
    This is a placeholder implementation for Phase 1.
    """
    logger.info("Logout attempt")
    
    # TODO: Implement actual logout logic
    
    return {"message": "Logged out successfully"}