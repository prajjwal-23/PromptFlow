"""
Lock Repository Implementation

This module provides the concrete implementation of the LockRepository
interface using Redis for distributed locking operations.
"""

from __future__ import annotations
from typing import Optional
import uuid
import logging
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from app.domain.execution.repositories import LockRepository
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LockRepositoryImpl(LockRepository):
    """Concrete implementation of LockRepository using Redis."""
    
    def __init__(self):
        """Initialize lock repository."""
        self.logger = logger
        self.settings = get_settings()
        self._client = None
        self._connected = False
    
    async def _get_client(self):
        """Get Redis client, creating connection if needed."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis is not available. Install redis-py to use distributed locking.")
        
        if not self._connected or self._client is None:
            try:
                self._client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    password=self.settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                
                # Test connection
                await self._client.ping()
                self._connected = True
                self.logger.info("Connected to Redis for distributed locking")
                
            except Exception as e:
                self.logger.error(f"Failed to connect to Redis: {e}")
                self._connected = False
                raise
        
        return self._client
    
    async def acquire_lock(
        self, 
        lock_key: str, 
        ttl: int = 30
    ) -> Optional[str]:
        """Acquire a distributed lock. Returns lock token if successful."""
        try:
            client = await self._get_client()
            
            # Generate unique token for this lock attempt
            token = str(uuid.uuid4())
            
            # Use Redis SET with NX and EX options for atomic lock acquisition
            # NX: Only set if key doesn't exist
            # EX: Set expiration in seconds
            result = await client.set(
                f"lock:{lock_key}",
                token,
                nx=True,
                ex=ttl
            )
            
            if result:
                self.logger.debug(f"Acquired lock {lock_key} with token {token}")
                return token
            else:
                self.logger.debug(f"Failed to acquire lock {lock_key} - already held")
                return None
                
        except Exception as e:
            self.logger.error(f"Error acquiring lock {lock_key}: {e}")
            return None
    
    async def release_lock(self, lock_key: str, lock_token: str) -> bool:
        """Release a distributed lock. Returns True if successful."""
        try:
            client = await self._get_client()
            
            # Use Lua script for atomic lock release
            # Only release if the token matches
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = await client.eval(
                lua_script,
                1,
                f"lock:{lock_key}",
                lock_token
            )
            
            success = result == 1
            
            if success:
                self.logger.debug(f"Released lock {lock_key} with token {lock_token}")
            else:
                self.logger.warning(f"Failed to release lock {lock_key} - token mismatch or lock not held")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error releasing lock {lock_key}: {e}")
            return False
    
    async def extend_lock(self, lock_key: str, lock_token: str, ttl: int) -> bool:
        """Extend a lock's TTL. Returns True if successful."""
        try:
            client = await self._get_client()
            
            # Use Lua script for atomic lock extension
            # Only extend if the token matches
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            
            result = await client.eval(
                lua_script,
                1,
                f"lock:{lock_key}",
                lock_token,
                ttl
            )
            
            success = result == 1
            
            if success:
                self.logger.debug(f"Extended lock {lock_key} with token {lock_token} for {ttl}s")
            else:
                self.logger.warning(f"Failed to extend lock {lock_key} - token mismatch or lock not held")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error extending lock {lock_key}: {e}")
            return False
    
    async def is_locked(self, lock_key: str) -> bool:
        """Check if a lock is currently held."""
        try:
            client = await self._get_client()
            result = await client.exists(f"lock:{lock_key}")
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error checking lock {lock_key}: {e}")
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


# In-memory lock implementation as fallback
class InMemoryLockRepositoryImpl(LockRepository):
    """In-memory lock implementation for development/testing."""
    
    def __init__(self):
        """Initialize in-memory lock repository."""
        self.logger = logger
        self._locks = {}
        self._lock_times = {}
    
    async def acquire_lock(
        self, 
        lock_key: str, 
        ttl: int = 30
    ) -> Optional[str]:
        """Acquire a distributed lock. Returns lock token if successful."""
        try:
            import time
            
            # Clean up expired locks
            await self._cleanup_expired_locks()
            
            # Check if lock is already held
            if lock_key in self._locks:
                return None
            
            # Generate unique token
            token = str(uuid.uuid4())
            
            # Acquire lock
            self._locks[lock_key] = token
            self._lock_times[lock_key] = time.time() + ttl
            
            self.logger.debug(f"Acquired in-memory lock {lock_key} with token {token}")
            return token
            
        except Exception as e:
            self.logger.error(f"Error acquiring in-memory lock {lock_key}: {e}")
            return None
    
    async def release_lock(self, lock_key: str, lock_token: str) -> bool:
        """Release a distributed lock. Returns True if successful."""
        try:
            # Check if lock exists and token matches
            if lock_key in self._locks and self._locks[lock_key] == lock_token:
                del self._locks[lock_key]
                if lock_key in self._lock_times:
                    del self._lock_times[lock_key]
                
                self.logger.debug(f"Released in-memory lock {lock_key} with token {lock_token}")
                return True
            else:
                self.logger.warning(f"Failed to release in-memory lock {lock_key} - token mismatch or lock not held")
                return False
                
        except Exception as e:
            self.logger.error(f"Error releasing in-memory lock {lock_key}: {e}")
            return False
    
    async def extend_lock(self, lock_key: str, lock_token: str, ttl: int) -> bool:
        """Extend a lock's TTL. Returns True if successful."""
        try:
            import time
            
            # Check if lock exists and token matches
            if lock_key in self._locks and self._locks[lock_key] == lock_token:
                self._lock_times[lock_key] = time.time() + ttl
                self.logger.debug(f"Extended in-memory lock {lock_key} with token {lock_token} for {ttl}s")
                return True
            else:
                self.logger.warning(f"Failed to extend in-memory lock {lock_key} - token mismatch or lock not held")
                return False
                
        except Exception as e:
            self.logger.error(f"Error extending in-memory lock {lock_key}: {e}")
            return False
    
    async def is_locked(self, lock_key: str) -> bool:
        """Check if a lock is currently held."""
        try:
            await self._cleanup_expired_locks()
            return lock_key in self._locks
            
        except Exception as e:
            self.logger.error(f"Error checking in-memory lock {lock_key}: {e}")
            return False
    
    async def _cleanup_expired_locks(self) -> None:
        """Clean up expired locks."""
        try:
            import time
            
            current_time = time.time()
            expired_keys = []
            
            for lock_key, expiry_time in self._lock_times.items():
                if current_time > expiry_time:
                    expired_keys.append(lock_key)
            
            for lock_key in expired_keys:
                del self._locks[lock_key]
                del self._lock_times[lock_key]
                self.logger.debug(f"Cleaned up expired in-memory lock {lock_key}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up expired locks: {e}")


def create_lock_repository() -> LockRepository:
    """Create appropriate lock repository based on availability."""
    if REDIS_AVAILABLE:
        try:
            return LockRepositoryImpl()
        except Exception as e:
            logger.warning(f"Redis not available, falling back to in-memory locks: {e}")
    
    logger.info("Using in-memory locks")
    return InMemoryLockRepositoryImpl()