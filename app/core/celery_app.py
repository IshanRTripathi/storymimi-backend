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

# Configure Celery with Redis reconnection bug fixes
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour time limit for tasks
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    
    # CRITICAL: Connection retry settings for Redis reconnection bug
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=None,  # Retry indefinitely
    broker_connection_retry_delay=5.0,   # Wait 5 seconds between retries
    
    # Redis transport options - CRITICAL for connection stability
    broker_transport_options={
        'visibility_timeout': 7200,      # 2 hours - longer than task timeout
        'retry_on_timeout': True,
        'socket_timeout': 120.0,         # 2 minutes socket timeout
        'socket_connect_timeout': 30.0,  # 30 seconds connect timeout
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPINTVL': 10,         # Send keepalive probes every 10 seconds
            'TCP_KEEPCNT': 6,            # Send up to 6 keepalive probes
            'TCP_KEEPIDLE': 60,          # Start keepalive after 60 seconds idle
        },
        'health_check_interval': 25,     # Health check every 25 seconds
        'max_connections': 20,           # Connection pool size
    },
    
    # Result backend transport options
    result_backend_transport_options={
        'retry_on_timeout': True,
        'socket_timeout': 120.0,
        'socket_connect_timeout': 30.0,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPINTVL': 10,
            'TCP_KEEPCNT': 6,
            'TCP_KEEPIDLE': 60,
        },
        'health_check_interval': 25,
        'max_connections': 20,
    },
    
    # Task settings for reliability
    task_acks_late=True,                 # Acknowledge after task completion
    worker_prefetch_multiplier=1,        # Prefetch only 1 task per worker
    task_reject_on_worker_lost=True,     # Reject tasks if worker is lost
    
    # Worker settings
    worker_disable_rate_limits=True,     # Disable rate limiting
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_log_color=False,
    
    # CRITICAL: Settings to prevent the Redis reconnection bug
    worker_cancel_long_running_tasks_on_connection_loss=True,  # Cancel tasks on connection loss
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