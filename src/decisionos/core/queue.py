from typing import Any, Dict, Protocol
from celery import Celery
import structlog

from decisionos.core.config import settings
from decisionos.worker.tasks import process_data_point

logger = structlog.get_logger()

class TaskQueue(Protocol):
    """
    Interface for background task dispatching.
    
    Why:
    - Decouples application logic from specific queue implementation (Celery/Redis).
    - Allows swapping implementations (e.g., in-memory for tests, SQS for cloud).
    """
    def enqueue_data_processing(self, data_point_id: str, payload: Dict[str, Any]) -> None:
        ...

class CeleryTaskQueue:
    """
    Redis-backed implementation using Celery.
    """
    def enqueue_data_processing(self, data_point_id: str, payload: Dict[str, Any]) -> None:
        """
        Dispatch processing task to Celery worker.
        
        Why:
        - .delay() is async and non-blocking.
        - Redis persistence ensures task survives app restarts.
        """
        logger.info("enqueueing_task", task="process_data_point", id=data_point_id)
        process_data_point.delay(data_point_id, payload)

# Global instance (singleton pattern)
# In a larger app, this would be injected via dependency injection
queue = CeleryTaskQueue()
