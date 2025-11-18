"""
Repository Factory Implementation

This module provides the concrete implementation of the RepositoryFactory
interface for creating repository instances with dependency injection.
"""

from __future__ import annotations
from typing import Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.execution.repositories import (
    RepositoryFactory,
    ExecutionRepository,
    EventRepository,
    NodeOutputRepository,
    CacheRepository,
    LockRepository,
    MetricsRepository
)
from .execution_repository import ExecutionRepositoryImpl
from .event_repository import EventRepositoryImpl
from .node_output_repository import NodeOutputRepositoryImpl
from .cache_repository import create_cache_repository
from .lock_repository import create_lock_repository
from .metrics_repository import create_metrics_repository
from app.core.database import async_session_maker
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepositoryFactoryImpl(RepositoryFactory):
    """Concrete implementation of RepositoryFactory."""
    
    def __init__(self, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        """Initialize repository factory."""
        self.session_factory = session_factory or async_session_maker
        self.logger = logger
        
        # Cache singleton instances for stateless repositories
        self._cache_repository: Optional[CacheRepository] = None
        self._lock_repository: Optional[LockRepository] = None
        self._metrics_repository: Optional[MetricsRepository] = None
    
    def create_execution_repository(self, session: Optional[AsyncSession] = None) -> ExecutionRepository:
        """Create execution repository instance."""
        try:
            if session is None:
                # Create a new session for standalone repository
                session = self.session_factory()
            
            return ExecutionRepositoryImpl(session)
            
        except Exception as e:
            self.logger.error(f"Error creating execution repository: {e}")
            raise
    
    def create_event_repository(self, session: Optional[AsyncSession] = None) -> EventRepository:
        """Create event repository instance."""
        try:
            if session is None:
                # Create a new session for standalone repository
                session = self.session_factory()
            
            return EventRepositoryImpl(session)
            
        except Exception as e:
            self.logger.error(f"Error creating event repository: {e}")
            raise
    
    def create_node_output_repository(self, session: Optional[AsyncSession] = None) -> NodeOutputRepository:
        """Create node output repository instance."""
        try:
            if session is None:
                # Create a new session for standalone repository
                session = self.session_factory()
            
            return NodeOutputRepositoryImpl(session)
            
        except Exception as e:
            self.logger.error(f"Error creating node output repository: {e}")
            raise
    
    def create_cache_repository(self) -> CacheRepository:
        """Create cache repository instance."""
        try:
            if self._cache_repository is None:
                self._cache_repository = create_cache_repository()
            
            return self._cache_repository
            
        except Exception as e:
            self.logger.error(f"Error creating cache repository: {e}")
            raise
    
    def create_lock_repository(self) -> LockRepository:
        """Create lock repository instance."""
        try:
            if self._lock_repository is None:
                self._lock_repository = create_lock_repository()
            
            return self._lock_repository
            
        except Exception as e:
            self.logger.error(f"Error creating lock repository: {e}")
            raise
    
    def create_metrics_repository(self) -> MetricsRepository:
        """Create metrics repository instance."""
        try:
            if self._metrics_repository is None:
                self._metrics_repository = create_metrics_repository()
            
            return self._metrics_repository
            
        except Exception as e:
            self.logger.error(f"Error creating metrics repository: {e}")
            raise
    
    async def create_all_repositories(self, session: Optional[AsyncSession] = None) -> dict:
        """Create all repository instances."""
        try:
            return {
                "execution": self.create_execution_repository(session),
                "event": self.create_event_repository(session),
                "node_output": self.create_node_output_repository(session),
                "cache": self.create_cache_repository(),
                "lock": self.create_lock_repository(),
                "metrics": self.create_metrics_repository(),
            }
            
        except Exception as e:
            self.logger.error(f"Error creating all repositories: {e}")
            raise
    
    async def close_all(self) -> None:
        """Close all repository connections."""
        try:
            if self._cache_repository and hasattr(self._cache_repository, 'close'):
                await self._cache_repository.close()
            
            if self._lock_repository and hasattr(self._lock_repository, 'close'):
                await self._lock_repository.close()
            
            if self._metrics_repository and hasattr(self._metrics_repository, 'close'):
                await self._metrics_repository.close()
            
            self.logger.info("All repository connections closed")
            
        except Exception as e:
            self.logger.error(f"Error closing repository connections: {e}")


# Global repository factory instance
_repository_factory: Optional[RepositoryFactoryImpl] = None


def get_repository_factory() -> RepositoryFactoryImpl:
    """Get the global repository factory."""
    global _repository_factory
    
    if _repository_factory is None:
        _repository_factory = RepositoryFactoryImpl()
    
    return _repository_factory


def create_repository_factory(
    session_factory: Optional[async_sessionmaker[AsyncSession]] = None
) -> RepositoryFactoryImpl:
    """Create a new repository factory instance."""
    return RepositoryFactoryImpl(session_factory)


# Repository provider for dependency injection
class RepositoryProvider:
    """Provider for repository instances with dependency injection."""
    
    def __init__(self, factory: Optional[RepositoryFactoryImpl] = None):
        """Initialize provider with factory."""
        self.factory = factory or get_repository_factory()
        self.logger = logger
    
    def get_execution_repository(self, session: Optional[AsyncSession] = None) -> ExecutionRepository:
        """Get execution repository."""
        return self.factory.create_execution_repository(session)
    
    def get_event_repository(self, session: Optional[AsyncSession] = None) -> EventRepository:
        """Get event repository."""
        return self.factory.create_event_repository(session)
    
    def get_node_output_repository(self, session: Optional[AsyncSession] = None) -> NodeOutputRepository:
        """Get node output repository."""
        return self.factory.create_node_output_repository(session)
    
    def get_cache_repository(self) -> CacheRepository:
        """Get cache repository."""
        return self.factory.create_cache_repository()
    
    def get_lock_repository(self) -> LockRepository:
        """Get lock repository."""
        return self.factory.create_lock_repository()
    
    def get_metrics_repository(self) -> MetricsRepository:
        """Get metrics repository."""
        return self.factory.create_metrics_repository()
    
    async def get_all_repositories(self, session: Optional[AsyncSession] = None) -> dict:
        """Get all repositories."""
        return await self.factory.create_all_repositories(session)


# Repository configuration
class RepositoryConfig:
    """Configuration for repositories."""
    
    def __init__(self):
        """Initialize configuration."""
        self.logger = logger
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load repository settings."""
        from app.core.config import get_settings
        settings = get_settings()
        
        return {
            "redis_host": getattr(settings, 'REDIS_HOST', 'localhost'),
            "redis_port": getattr(settings, 'REDIS_PORT', 6379),
            "redis_db": getattr(settings, 'REDIS_DB', 0),
            "redis_password": getattr(settings, 'REDIS_PASSWORD', None),
            "cache_ttl": getattr(settings, 'CACHE_TTL', 3600),
            "lock_ttl": getattr(settings, 'LOCK_TTL', 30),
            "metrics_retention_days": getattr(settings, 'METRICS_RETENTION_DAYS', 30),
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis configuration."""
        return {
            "host": self.settings["redis_host"],
            "port": self.settings["redis_port"],
            "db": self.settings["redis_db"],
            "password": self.settings["redis_password"],
        }
    
    def get_cache_config(self) -> dict:
        """Get cache configuration."""
        return {
            "ttl": self.settings["cache_ttl"],
        }
    
    def get_lock_config(self) -> dict:
        """Get lock configuration."""
        return {
            "ttl": self.settings["lock_ttl"],
        }
    
    def get_metrics_config(self) -> dict:
        """Get metrics configuration."""
        return {
            "retention_days": self.settings["metrics_retention_days"],
        }


# Repository health check
class RepositoryHealthCheck:
    """Health check for all repositories."""
    
    def __init__(self, provider: Optional[RepositoryProvider] = None):
        """Initialize health check."""
        self.provider = provider or RepositoryProvider()
        self.logger = logger
    
    async def check_all_repositories(self) -> dict:
        """Check health of all repositories."""
        try:
            health_status = {
                "overall": "healthy",
                "repositories": {}
            }
            
            # Check cache repository
            try:
                cache_repo = self.provider.get_cache_repository()
                await cache_repo.set("health_check", "test", ttl=10)
                value = await cache_repo.get("health_check")
                await cache_repo.delete("health_check")
                
                health_status["repositories"]["cache"] = {
                    "status": "healthy" if value == "test" else "unhealthy",
                    "message": "Cache repository is operational"
                }
            except Exception as e:
                health_status["repositories"]["cache"] = {
                    "status": "unhealthy",
                    "message": str(e)
                }
                health_status["overall"] = "unhealthy"
            
            # Check lock repository
            try:
                lock_repo = self.provider.get_lock_repository()
                token = await lock_repo.acquire_lock("health_check", ttl=10)
                if token:
                    released = await lock_repo.release_lock("health_check", token)
                    health_status["repositories"]["lock"] = {
                        "status": "healthy" if released else "unhealthy",
                        "message": "Lock repository is operational"
                    }
                else:
                    health_status["repositories"]["lock"] = {
                        "status": "unhealthy",
                        "message": "Failed to acquire test lock"
                    }
                    health_status["overall"] = "unhealthy"
            except Exception as e:
                health_status["repositories"]["lock"] = {
                    "status": "unhealthy",
                    "message": str(e)
                }
                health_status["overall"] = "unhealthy"
            
            # Check metrics repository
            try:
                metrics_repo = self.provider.get_metrics_repository()
                await metrics_repo.record_metric("health_check", 1.0)
                health_status["repositories"]["metrics"] = {
                    "status": "healthy",
                    "message": "Metrics repository is operational"
                }
            except Exception as e:
                health_status["repositories"]["metrics"] = {
                    "status": "unhealthy",
                    "message": str(e)
                }
                health_status["overall"] = "unhealthy"
            
            # Check database repositories
            try:
                from app.execution.store.unit_of_work import get_uow_factory
                uow_factory = get_uow_factory()
                from app.execution.store.unit_of_work import UnitOfWorkHealthCheck
                health_checker = UnitOfWorkHealthCheck(uow_factory)
                db_health = await health_checker.check_health()
                
                health_status["repositories"]["database"] = db_health
                
                if db_health.get("status") != "healthy":
                    health_status["overall"] = "unhealthy"
                    
            except Exception as e:
                health_status["repositories"]["database"] = {
                    "status": "unhealthy",
                    "message": str(e)
                }
                health_status["overall"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Repository health check failed: {e}")
            return {
                "overall": "unhealthy",
                "error": str(e)
            }


# Factory functions for easy access
def create_repository_provider() -> RepositoryProvider:
    """Create repository provider."""
    return RepositoryProvider()


def create_repository_health_check() -> RepositoryHealthCheck:
    """Create repository health check."""
    return RepositoryHealthCheck()


def get_repository_config() -> RepositoryConfig:
    """Get repository configuration."""
    return RepositoryConfig()