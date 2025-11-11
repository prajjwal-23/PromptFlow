"""
Rate limiting middleware using Redis.
"""

import time
import json
from typing import Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware based on IP address."""
    
    def __init__(self, app, calls: int = settings.RATE_LIMIT_PER_MINUTE, period: int = 60):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            calls: Number of allowed requests per period
            period: Time period in seconds
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.redis = None  # TODO: Initialize Redis client
        
    async def dispatch(self, request: Request, call_next):
        """Handle rate limiting."""
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        if not client_ip:
            # If we can't get IP, skip rate limiting
            return await call_next(request)
        
        # Check rate limit
        if await self._is_rate_limited(client_ip):
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=request.url.path,
                method=request.method
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        if self.redis:
            remaining = await self._get_remaining_calls(client_ip)
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
        
        return response
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client IP
        return request.client.host if request.client else None
    
    async def _is_rate_limited(self, ip: str) -> bool:
        """Check if IP is rate limited."""
        if not self.redis:
            return False
        
        try:
            key = f"rate_limit:{ip}"
            
            # Get current count
            current = await self.redis.get(key)
            if current is None:
                # First request in window
                await self.redis.setex(key, self.period, 1)
                return False
            
            current_count = int(current)
            
            if current_count >= self.calls:
                return True
            
            # Increment counter
            await self.redis.incr(key)
            return False
            
        except Exception as e:
            logger.error("Rate limiting error", error=str(e))
            return False
    
    async def _get_remaining_calls(self, ip: str) -> int:
        """Get remaining calls for IP."""
        if not self.redis:
            return self.calls
        
        try:
            key = f"rate_limit:{ip}"
            current = await self.redis.get(key)
            if current is None:
                return self.calls
            
            current_count = int(current)
            return max(0, self.calls - current_count)
            
        except Exception:
            return self.calls