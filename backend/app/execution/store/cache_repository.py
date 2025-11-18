"""
Cache Repository Implementation

This module provides the concrete implementation of the CacheRepository
interface using Redis for caching operations.
"""

from __future__ import annotations
from typing import Any, Optional
import json
import logging
import pickle

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from app.domain.execution.repositories import CacheRepository
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheRepositoryImpl(CacheRepository):
    """Concrete implementation of CacheRepository using Redis."""
    
    def __init__(self):
        """Initialize cache repository."""
        self.logger = logger
        self.settings = get_settings()
        self._client = None
        self._connected = False
    
    async def _get_client(self):
        """Get Redis client, creating connection if needed."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install redis-py to use caching.")
        
        if not self._connected or self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    password=self.settings.REDIS_PASSWORD,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                
                # Test connection
                await self._client.ping()
                self._connected = True
                self.logger.info("Connected to Redis cache")
                
            except Exception as e:
                self.logger.error(f"Failed to connect to Redis: {e}")
                self._connected = False
                raise
        
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            client = await self._get_client()
            
            # Try to get value
            value = await client.get(key)
            
            if value is None:
                return None
            
            # Deserialize value
            try:
                # Try JSON first
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(value)
            
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        try:
            client = await self._get_client()
            
            # Serialize value
            try:
                # Try JSON first for better performance
                serialized = json.dumps(value, default=str).encode('utf-8')
            except (TypeError, ValueError):
                # Fall back to pickle for complex objects
                serialized = pickle.dumps(value)
            
            # Set with TTL if provided
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)
            
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            client = await self._get_client()
            result = await client.delete(key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        try:
            client = await self._get_client()
            await client.flushdb()
            self.logger.info("Cache cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            client = await self._get_client()
            result = await client.exists(key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        try:
            if self._client and self._connected:
                await self._client.close()
                self._connected = False
                self.logger.info("Redis connection closed")
                
        except Exception as e:
            self.logger.error(f"Error closing Redis connection: {e}")


# In-memory cache implementation as fallback
class InMemoryCacheRepositoryImpl(CacheRepository):
    """In-memory cache implementation for development/testing."""
    
    def __init__(self):
        """Initialize in-memory cache."""
        self.logger = logger
        self._cache = {}
        self._ttl_cache = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            # Check if key exists and hasn't expired
            if key in self._cache:
                if key in self._ttl_cache:
                    import time
                    if time.time() > self._ttl_cache[key]:
                        await self.delete(key)
                        return None
                return self._cache[key]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        try:
            self._cache[key] = value
            
            if ttl:
                import time
                self._ttl_cache[key] = time.time() + ttl
            elif key in self._ttl_cache:
                del self._ttl_cache[key]
                
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            existed = key in self._cache
            
            if key in self._cache:
                del self._cache[key]
            if key in self._ttl_cache:
                del self._ttl_cache[key]
            
            return existed
            
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self._cache.clear()
            self._ttl_cache.clear()
            self.logger.info("In-memory cache cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if key in self._cache:
                if key in self._ttl_cache:
                    import time
                    if time.time() > self._ttl_cache[key]:
                        await self.delete(key)
                        return False
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {e}")
            return False


def create_cache_repository() -> CacheRepository:
    """Create appropriate cache repository based on availability."""
    if REDIS_AVAILABLE:
        try:
            return CacheRepositoryImpl()
        except Exception as e:
            logger.warning(f"Redis not available, falling back to in-memory cache: {e}")
    
    logger.info("Using in-memory cache")
    return InMemoryCacheRepositoryImpl()