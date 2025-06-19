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

# CRITICAL FIX: Comprehensive configuration to address Celery 5.x Redis reconnection bug
# This is based on extensive research and addresses the well-known GitHub issue #7276
celery_app.conf.update(
    # Basic serialization settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    
    # Task execution settings
    task_time_limit=3600,  # 1 hour time limit for tasks
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks to prevent memory leaks
    
    # CRITICAL: Connection retry settings - prevents indefinite task freeze
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=None,  # Retry indefinitely (critical for Cloud Run)
    broker_connection_retry_delay=1.0,
    
    # CRITICAL: Redis-specific transport options to fix reconnection bug
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour - prevents tasks from timing out
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPIDLE': 1,      # Start keepalive after 1 second of inactivity
            'TCP_KEEPINTVL': 3,     # Send keepalive every 3 seconds
            'TCP_KEEPCNT': 5,       # Send up to 5 keepalive probes
        },
        'health_check_interval': 30,  # Check connection health every 30 seconds
        'connection_pool_kwargs': {
            'max_connections': 20,
            'retry_on_timeout': True,
            'socket_timeout': 5.0,
            'socket_connect_timeout': 5.0,
        },
    },
    
    # CRITICAL: Result backend connection settings
    result_backend_transport_options={
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPIDLE': 1,
            'TCP_KEEPINTVL': 3,
            'TCP_KEEPCNT': 5,
        },
        'health_check_interval': 30,
        'connection_pool_kwargs': {
            'max_connections': 20,
            'retry_on_timeout': True,
            'socket_timeout': 5.0,
            'socket_connect_timeout': 5.0,
        },
    },
    
    # CRITICAL: Task acknowledgment settings to prevent task loss
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_prefetch_multiplier=1,  # Process one task at a time (critical for reliability)
    
    # CRITICAL: Connection management settings
    broker_heartbeat=30,  # Send heartbeat every 30 seconds
    broker_pool_limit=10,  # Limit connection pool size
    
    # CRITICAL: Worker behavior settings to prevent connection issues
    worker_cancel_long_running_tasks_on_connection_loss=True,
    task_reject_on_worker_lost=False,  # Don't reject tasks on worker loss
    
    # Additional reliability settings
    task_default_queue="default",
    task_routes={
        'story_task.generate': {'queue': 'default'},
    },
    
    # Connection cleanup settings
    broker_connection_timeout=10,
    result_backend_connection_timeout=10,
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