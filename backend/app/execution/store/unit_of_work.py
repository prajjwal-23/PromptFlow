"""
Unit of Work Implementation

This module provides the concrete implementation of the UnitOfWork
interface for transaction management following the Unit of Work pattern.
"""

from __future__ import annotations
from typing import Optional
import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.domain.execution.repositories import (
    UnitOfWork,
    ExecutionRepository,
    EventRepository,
    NodeOutputRepository
)
from app.execution.store import (
    ExecutionRepositoryImpl,
    EventRepositoryImpl,
    NodeOutputRepositoryImpl
)
from app.core.database import get_async_session
from app.core.logging import get_logger

logger = get_logger(__name__)


class UnitOfWorkImpl(UnitOfWork):
    """Concrete implementation of UnitOfWork using SQLAlchemy."""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """Initialize Unit of Work with session factory."""
        self.session_factory = session_factory
        self.logger = logger
        self._session: Optional[AsyncSession] = None
        self._execution_repo: Optional[ExecutionRepository] = None
        self._event_repo: Optional[EventRepository] = None
        self._node_output_repo: Optional[NodeOutputRepository] = None
        self._active = False
    
    async def __aenter__(self):
        """Enter unit of work context."""
        try:
            self._session = self.session_factory()
            self._active = True
            
            # Initialize repositories with the session
            self._execution_repo = ExecutionRepositoryImpl(self._session)
            self._event_repo = EventRepositoryImpl(self._session)
            self._node_output_repo = NodeOutputRepositoryImpl(self._session)
            
            self.logger.debug("Unit of Work started")
            return self
            
        except Exception as e:
            self.logger.error(f"Error starting Unit of Work: {e}")
            await self._cleanup()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit unit of work context."""
        try:
            if not self._active:
                return
            
            if exc_type is not None:
                # Exception occurred, rollback
                await self.rollback()
                self.logger.error(f"Unit of Work rolled back due to exception: {exc_val}")
            else:
                # No exception, commit
                await self.commit()
                self.logger.debug("Unit of Work committed successfully")
            
        except Exception as e:
            self.logger.error(f"Error ending Unit of Work: {e}")
            try:
                await self.rollback()
            except Exception as rollback_error:
                self.logger.error(f"Error during rollback: {rollback_error}")
        finally:
            await self._cleanup()
    
    async def commit(self) -> None:
        """Commit transaction."""
        try:
            if not self._active or not self._session:
                raise RuntimeError("Unit of Work is not active")
            
            await self._session.commit()
            self.logger.debug("Transaction committed")
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during commit: {e}")
            await self.rollback()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during commit: {e}")
            await self.rollback()
            raise
    
    async def rollback(self) -> None:
        """Rollback transaction."""
        try:
            if not self._active or not self._session:
                return
            
            await self._session.rollback()
            self.logger.debug("Transaction rolled back")
            
        except Exception as e:
            self.logger.error(f"Error during rollback: {e}")
            raise
    
    def get_execution_repository(self) -> ExecutionRepository:
        """Get execution repository."""
        if not self._active or not self._execution_repo:
            raise RuntimeError("Unit of Work is not active")
        return self._execution_repo
    
    def get_event_repository(self) -> EventRepository:
        """Get event repository."""
        if not self._active or not self._event_repo:
            raise RuntimeError("Unit of Work is not active")
        return self._event_repo
    
    def get_node_output_repository(self) -> NodeOutputRepository:
        """Get node output repository."""
        if not self._active or not self._node_output_repo:
            raise RuntimeError("Unit of Work is not active")
        return self._node_output_repo
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self._session:
                await self._session.close()
                self._session = None
            
            self._execution_repo = None
            self._event_repo = None
            self._node_output_repo = None
            self._active = False
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class UnitOfWorkFactory:
    """Factory for creating Unit of Work instances."""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """Initialize factory with session factory."""
        self.session_factory = session_factory
        self.logger = logger
    
    def create_unit_of_work(self) -> UnitOfWork:
        """Create a new Unit of Work instance."""
        return UnitOfWorkImpl(self.session_factory)
    
    @asynccontextmanager
    async def unit_of_work(self):
        """Context manager for Unit of Work."""
        uow = self.create_unit_of_work()
        async with uow:
            yield uow


# Global Unit of Work factory instance
_uow_factory: Optional[UnitOfWorkFactory] = None


def get_uow_factory() -> UnitOfWorkFactory:
    """Get the global Unit of Work factory."""
    global _uow_factory
    
    if _uow_factory is None:
        from app.core.database import async_session_maker
        _uow_factory = UnitOfWorkFactory(async_session_maker)
    
    return _uow_factory


async def get_unit_of_work() -> UnitOfWork:
    """Get a Unit of Work instance."""
    factory = get_uow_factory()
    return factory.create_unit_of_work()


@asynccontextmanager
async def unit_of_work_context():
    """Context manager for Unit of Work."""
    factory = get_uow_factory()
    async with factory.unit_of_work() as uow:
        yield uow


# Transaction management utilities
class TransactionManager:
    """Utility class for transaction management."""
    
    def __init__(self, uow_factory: UnitOfWorkFactory):
        """Initialize with Unit of Work factory."""
        self.uow_factory = uow_factory
        self.logger = logger
    
    async def execute_in_transaction(self, func, *args, **kwargs):
        """Execute a function within a transaction."""
        async with self.uow_factory.unit_of_work() as uow:
            try:
                result = await func(uow, *args, **kwargs)
                return result
            except Exception as e:
                self.logger.error(f"Transaction failed: {e}")
                raise
    
    async def execute_read_only(self, func, *args, **kwargs):
        """Execute a read-only operation."""
        async with self.uow_factory.unit_of_work() as uow:
            try:
                result = await func(uow, *args, **kwargs)
                # No commit needed for read-only operations
                return result
            except Exception as e:
                self.logger.error(f"Read-only operation failed: {e}")
                raise


# Repository base class with common functionality
class BaseRepository:
    """Base repository with common functionality."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session."""
        self.session = session
        self.logger = logger
    
    async def _handle_exception(self, operation: str, error: Exception) -> None:
        """Handle repository exceptions."""
        self.logger.error(f"Error in {operation}: {error}")
        raise
    
    async def _validate_session(self) -> None:
        """Validate that session is active."""
        if self.session is None:
            raise RuntimeError("Repository session is not initialized")


# Health check for Unit of Work
class UnitOfWorkHealthCheck:
    """Health check for Unit of Work and repositories."""
    
    def __init__(self, uow_factory: UnitOfWorkFactory):
        """Initialize with Unit of Work factory."""
        self.uow_factory = uow_factory
        self.logger = logger
    
    async def check_health(self) -> dict:
        """Check health of Unit of Work and repositories."""
        try:
            async with self.uow_factory.unit_of_work() as uow:
                # Test execution repository
                execution_repo = uow.get_execution_repository()
                count = await execution_repo.get_execution_count()
                
                # Test event repository
                event_repo = uow.get_event_repository()
                event_count = await event_repo.get_event_count()
                
                return {
                    "status": "healthy",
                    "execution_count": count,
                    "event_count": event_count,
                    "database": "connected"
                }
                
        except Exception as e:
            self.logger.error(f"Unit of Work health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": "disconnected"
            }


def create_transaction_manager() -> TransactionManager:
    """Create transaction manager."""
    factory = get_uow_factory()
    return TransactionManager(factory)


def create_health_check() -> UnitOfWorkHealthCheck:
    """Create health check."""
    factory = get_uow_factory()
    return UnitOfWorkHealthCheck(factory)