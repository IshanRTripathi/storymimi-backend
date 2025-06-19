from celery import Celery
from app.core.config.settings import settings
import logging
import socket
import ssl

# Configure logging for Celery
# Suppress timer logs by setting log level for specific loggers
logging.getLogger('celery.worker').setLevel(logging.INFO)
logging.getLogger('celery.timer').setLevel(logging.WARNING)
logging.getLogger('celery.beat').setLevel(logging.INFO)

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
    
    # Task reliability settings - CRITICAL for Cloud Run
    task_acks_late=True,                    # Acknowledge tasks only after completion
    worker_prefetch_multiplier=1,           # Fetch one task at a time to prevent loss
    task_reject_on_worker_lost=True,        # Reject tasks if worker connection is lost
    
    # Task execution settings optimized for Cloud Run
    task_track_started=True,
    task_time_limit=3600,                   # 1 hour time limit for long AI tasks
    task_soft_time_limit=3300,              # 55 minutes soft limit
    worker_max_tasks_per_child=100,         # Restart worker after 100 tasks to prevent memory leaks
    worker_disable_rate_limits=True,        # Disable rate limits for better performance
    
    # Connection settings optimized for managed Redis
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,       # Limit retries to prevent infinite loops
    broker_connection_retry_delay=2.0,      # Longer delay between retries
    
    # Heartbeat and health check settings for Cloud Run
    broker_heartbeat=60,                    # Heartbeat every 60 seconds
    broker_pool_limit=5,                    # Smaller pool for Cloud Run
    
    # Result backend settings optimized for reliability
    result_backend_transport_options={
        'visibility_timeout': 3600,
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            socket.TCP_KEEPIDLE: 300,       # 5 minutes keepalive
            socket.TCP_KEEPINTVL: 60,       # Check every 60 seconds
            socket.TCP_KEEPCNT: 5,          # 5 failed checks before disconnect
        },
        'health_check_interval': 60,
        'connection_pool_kwargs': {
            'max_connections': 5,
            'retry_on_timeout': True,
            'socket_timeout': 30,
            'socket_connect_timeout': 10,
        }
    },
    
    # Broker transport options for better Cloud Run performance
    broker_transport_options={
        'visibility_timeout': 3600,
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            socket.TCP_KEEPIDLE: 300,       # 5 minutes keepalive
            socket.TCP_KEEPINTVL: 60,       # Check every 60 seconds  
            socket.TCP_KEEPCNT: 5,          # 5 failed checks before disconnect
        },
        'health_check_interval': 60,
        'max_connections': 5,
        'connection_pool_kwargs': {
            'max_connections': 5,
            'retry_on_timeout': True, 
            'socket_timeout': 30,
            'socket_connect_timeout': 10,
        }
    },
    
    # Worker settings optimized for Cloud Run
    worker_send_task_events=False,          # Disable events to reduce overhead
    task_send_sent_event=False,             # Disable sent events
    worker_hijack_root_logger=False,        # Don't hijack root logger
    
    # Task routing settings
    task_routes={
        'app.tasks.*': {'queue': 'storymimi'}
    },
    
    # Queue settings
    task_default_queue='storymimi',
    task_default_exchange='storymimi',
    task_default_exchange_type='direct',
    task_default_routing_key='storymimi',
    
    # Optimization for Cloud Run environment
    task_compression='gzip',                # Compress large task payloads
    result_compression='gzip',              # Compress results
    worker_log_color=False,                 # Disable colors for Cloud Logging
    
    # Security settings
    task_always_eager=False,                # Never run tasks synchronously
    task_eager_propagates=False,            # Don't propagate exceptions in eager mode
    
    # Memory optimization
    result_expires=3600,                    # Results expire after 1 hour
    task_ignore_result=False,               # We need results for story generation
    
    # Advanced worker settings for stability
    worker_max_memory_per_child=512000,     # 512MB max memory per child (Cloud Run optimization)
    worker_proc_alive_timeout=60,           # 60 seconds timeout for worker processes
)

# Configure beat scheduler (if needed)
celery_app.conf.beat_schedule = {
    # Add periodic tasks here if needed
}

# Autodiscover tasks
celery_app.autodiscover_tasks(['app.tasks'])

# Add error handling for Cloud Run specific issues
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test worker connectivity"""
    print(f'Request: {self.request!r}')
    return "Worker is healthy and responsive"