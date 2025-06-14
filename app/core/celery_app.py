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

# Configure Celery to automatically discover tasks
celery_app.conf.task_routes = {
    'app.tasks.*': {'queue': 'storymimi'}
}

celery_app.conf.beat_schedule = {
    # Add periodic tasks here if needed
}

# Add autodiscover tasks
celery_app.autodiscover_tasks(['app.tasks'])