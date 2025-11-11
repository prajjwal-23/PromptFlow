"""
Logging configuration for the application.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """Setup structured logging for the application."""
    
    # Configure standard logging
    log_format = "%(message)s"
    if settings.LOG_FORMAT == "json":
        log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
    
    logging.basicConfig(
        format=log_format,
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure structlog with simpler setup for compatibility
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add formatter based on LOG_FORMAT
    if settings.LOG_FORMAT == "json":
        try:
            processors.append(
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
                    jsonlogger.JsonFormatter(),
                )
            )
        except Exception:
            # Fallback to console renderer if JSON formatter fails
            processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # Setup structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set JSON formatter for standard logging if needed
    if settings.LOG_FORMAT == "json":
        try:
            formatter = jsonlogger.JsonFormatter()
            for handler in logging.root.handlers[:]:
                handler.setFormatter(formatter)
        except Exception:
            pass  # Keep default formatter if JSON fails


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Create a default logger
logger = get_logger(__name__)


class LoggerMixin:
    """Mixin for classes that need logging capabilities."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for the class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


def log_request(request_data: Dict[str, Any]) -> None:
    """Log HTTP request data."""
    logger.info("HTTP request", **request_data)


def log_response(response_data: Dict[str, Any]) -> None:
    """Log HTTP response data."""
    logger.info("HTTP response", **response_data)


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log error with context."""
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **(context or {})
    )