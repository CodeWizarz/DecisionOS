import structlog
import logging
import uuid
from fastapi import Request, Response
from decisionos.core.config import settings

def configure_logging() -> None:
    """
    Configure structured logging for production.
    
    Why:
    - Structured logs (JSON) are essential for querying in scalable systems (e.g. ELK, Datadog).
    - Standardizes log format across all services.
    - Handles async context variables (trace IDs) if needed.
    """
    processors = [
        structlog.contextvars.merge_contextvars, # Support for correlation IDs
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if settings.ENV == "production" else structlog.dev.ConsoleRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Redirect standard library logging to structlog
    logging.basicConfig(format="%(message)s", level=settings.LOG_LEVEL)


# Logging Middleware abstraction
# Why? To ensure every request has a unique trace ID for debugging distributed systems.
async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    
    # Generate or propagate request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    
    # Add request ID to response headers for client visibility
    response.headers["X-Request-ID"] = request_id
    
    return response
