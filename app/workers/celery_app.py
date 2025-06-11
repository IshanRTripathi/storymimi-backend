from celery import Celery
from app.config import settings

# Create the Celery application
celery_app = Celery(
    "storymimi",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour time limit for tasks
    worker_max_tasks_per_child=200,  # Restart worker after 200 tasks
    broker_connection_retry_on_startup=True,
)

# Import tasks to ensure they are registered with Celery
# This import is placed here to avoid circular imports
from app.workers import story_worker  # noqa