from celery import Celery
from app.core.config.settings import settings
import logging
import socket

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
    
    # Task reliability settings (CRITICAL for Redis reconnection bug)
    task_acks_late=True,                    # CRITICAL: Acknowledge tasks only after completion
    worker_prefetch_multiplier=1,           # CRITICAL: Fetch one task at a time to prevent loss
    task_reject_on_worker_lost=True,        # CRITICAL: Reject tasks if worker connection is lost
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,                   # 1 hour time limit for tasks
    task_soft_time_limit=3300,              # 55 minutes soft limit
    worker_max_tasks_per_child=1000,        # Restart worker after 1000 tasks
    
    # Connection retry settings (CRITICAL for Redis reconnection)
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=None,     # CRITICAL: Infinite retries
    broker_connection_retry_delay=1.0,
    
    # Heartbeat and health check settings
    broker_heartbeat=None,                  # CRITICAL: Disable heartbeat to prevent reconnection issues
    broker_pool_limit=10,
    
    # Result backend connection settings with proper socket options
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            socket.TCP_KEEPIDLE: 1,         # FIXED: Use socket constants, not strings
            socket.TCP_KEEPINTVL: 1,        # FIXED: Use socket constants, not strings
            socket.TCP_KEEPCNT: 3,          # FIXED: Use socket constants, not strings
        },
        'health_check_interval': 30,
    },
    
    # Broker transport options with proper socket configuration  
    broker_transport_options={
        'visibility_timeout': 3600,
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            socket.TCP_KEEPIDLE: 1,         # FIXED: Use socket constants, not strings
            socket.TCP_KEEPINTVL: 1,        # FIXED: Use socket constants, not strings
            socket.TCP_KEEPCNT: 3,          # FIXED: Use socket constants, not strings
        },
        'health_check_interval': 30,
        'max_connections': 10,
    },
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