import structlog
import logging
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
        structlog.contextvars.merge_contextvars,
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
