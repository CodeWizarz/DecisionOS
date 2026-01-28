from celery import Celery
from decisionos.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["decisionos.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Production settings for reliability
    task_acks_late=True,  # Only ack after success
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Prevent hogging tasks for fair distribution
)

if __name__ == "__main__":
    celery_app.start()
