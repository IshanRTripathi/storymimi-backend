from celery import Celery
from app.core.config.settings import settings
import logging

# Configure logging for Celery
# Suppress timer logs by setting log level for specific loggers
logging.getLogger('celery.worker').setLevel(logging.INFO)
logging.getLogger('celery.timer').setLevel(logging.INFO)

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
    # Set worker log level to INFO
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_log_color=False,  # Disable color for better log filtering
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