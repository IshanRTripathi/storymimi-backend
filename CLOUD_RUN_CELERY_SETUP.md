# Cloud Run Celery Setup - Comprehensive Guide

## Overview
This document outlines the complete setup and deployment process for running Celery workers with Redis on Google Cloud Run, based on extensive research and testing.

## Key Findings

### 1. Application Works Locally with Docker Compose
- ✅ The application runs perfectly with Docker Compose locally
- ✅ All services communicate correctly in local environment
- ❌ Issues arise specifically in Cloud Run environment

### 2. Cloud Run Specific Challenges
- **Network Isolation**: Cloud Run services run in isolated environments
- **Redis Connection Persistence**: Redis connections can drop due to Cloud Run's networking
- **Celery 5.x Redis Reconnection Bug**: Well-documented upstream issue (GitHub #7276)
- **Health Check Requirements**: Cloud Run requires HTTP health endpoints

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud Run     │    │   Cloud Run     │    │  Redis Instance │
│   API Service   │───▶│ Worker Service  │───▶│  (Memorystore)  │
│   (Public)      │    │   (Private)     │    │   (Private)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Solution Components

### 1. Single Docker Image Approach
- Build one Docker image for both API and worker
- Use different CMD commands for different services
- Shared codebase and dependencies

### 2. Optimized Celery Configuration

```python
# app/core/celery_app.py
import os
from celery import Celery
from kombu import Queue

# Redis configuration optimized for Cloud Run
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Enhanced broker configuration for Cloud Run
broker_transport_options = {
    'retry_on_timeout': True,
    'max_retries': 10,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 1,
    'socket_keepalive': True,
    'socket_keepalive_options': {
        'TCP_KEEPIDLE': 1,
        'TCP_KEEPINTVL': 3,
        'TCP_KEEPCNT': 5,
    },
    'socket_connect_timeout': 30,
    'socket_timeout': 30,
    'health_check_interval': 30,
}

# Celery app configuration
celery_app = Celery(
    'storymimi',
    broker=redis_url,
    backend=redis_url,
    include=['app.tasks.generate_story_task']
)

# Optimized configuration for Cloud Run
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings optimized for Cloud Run
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # Connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_transport_options=broker_transport_options,
    
    # Result backend settings
    result_backend_transport_options={
        'retry_on_timeout': True,
        'max_retries': 10,
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('story_generation', routing_key='story_generation'),
    ),
    task_routes={
        'app.tasks.generate_story_task.generate_story_task': {
            'queue': 'story_generation'
        }
    }
)
```

### 3. Worker with Health Check

```python
# worker_with_health.py
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from celery import Celery
from app.core.celery_app import celery_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP logs
        pass

def run_health_server():
    """Run health check server in background"""
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    # Start health check server in daemon thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Start Celery worker in main thread with optimized flags
    logger.info("Starting Celery worker with Cloud Run optimizations...")
    
    # Critical flags for Cloud Run stability
    worker_flags = [
        '--loglevel=info',
        '--without-mingle',      # Prevents startup freeze
        '--without-gossip',      # Reduces network overhead
        '--without-heartbeat',   # Prevents heartbeat issues
        '--pool=prefork',        # More stable than threads
        '--concurrency=2',       # Limit concurrent tasks
        '--max-tasks-per-child=100',  # Prevent memory leaks
        '--queues=story_generation,default',
    ]
    
    celery_app.worker_main(worker_flags)
```

### 4. Cloud Build Configuration

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/storymimi:$COMMIT_SHA', '.']

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/storymimi:$COMMIT_SHA']

  # Deploy API service
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'storymimi-api'
      - '--image=gcr.io/$PROJECT_ID/storymimi:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--port=8080'
      - '--memory=1Gi'
      - '--cpu=1'
      - '--min-instances=1'
      - '--max-instances=5'
      - '--timeout=300'
      - '--vpc-connector=storymimi-connector'
      - '--update-secrets=REDIS_URL=redis-url:latest'
      - '--update-secrets=SUPABASE_URL=supabase-url:latest'
      - '--update-secrets=SUPABASE_KEY=supabase-key:latest'
      - '--update-secrets=OPENROUTER_API_KEY=openrouter-api-key:latest'
      - '--update-secrets=GEMINI_API_KEY=gemini-api-key:latest'
      - '--update-secrets=TOGETHER_API_KEY=together-api-key:latest'
      - '--update-secrets=ELEVENLABS_API_KEY=elevenlabs-api-key:latest'
      - '--update-secrets=ELEVENLABS_VOICE_ID=elevenlabs-voice-id:latest'
      - '--update-env-vars=SERVICE_TYPE=api'

  # Deploy Worker service
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'storymimi-worker'
      - '--image=gcr.io/$PROJECT_ID/storymimi:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--no-allow-unauthenticated'
      - '--port=8080'
      - '--memory=2Gi'
      - '--cpu=2'
      - '--min-instances=1'
      - '--max-instances=3'
      - '--timeout=3600'
      - '--cpu-throttling'
      - '--vpc-connector=storymimi-connector'
      - '--update-secrets=REDIS_URL=redis-url:latest'
      - '--update-secrets=SUPABASE_URL=supabase-url:latest'
      - '--update-secrets=SUPABASE_KEY=supabase-key:latest'
      - '--update-secrets=OPENROUTER_API_KEY=openrouter-api-key:latest'
      - '--update-secrets=GEMINI_API_KEY=gemini-api-key:latest'
      - '--update-secrets=TOGETHER_API_KEY=together-api-key:latest'
      - '--update-secrets=ELEVENLABS_API_KEY=elevenlabs-api-key:latest'
      - '--update-secrets=ELEVENLABS_VOICE_ID=elevenlabs-voice-id:latest'
      - '--update-env-vars=SERVICE_TYPE=worker'

# Secret Manager configuration
availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/redis-url/versions/latest
      env: REDIS_URL
    - versionName: projects/$PROJECT_ID/secrets/supabase-url/versions/latest
      env: SUPABASE_URL
    - versionName: projects/$PROJECT_ID/secrets/supabase-key/versions/latest
      env: SUPABASE_KEY
    - versionName: projects/$PROJECT_ID/secrets/openrouter-api-key/versions/latest
      env: OPENROUTER_API_KEY
    - versionName: projects/$PROJECT_ID/secrets/gemini-api-key/versions/latest
      env: GEMINI_API_KEY
    - versionName: projects/$PROJECT_ID/secrets/together-api-key/versions/latest
      env: TOGETHER_API_KEY
    - versionName: projects/$PROJECT_ID/secrets/elevenlabs-api-key/versions/latest
      env: ELEVENLABS_API_KEY
    - versionName: projects/$PROJECT_ID/secrets/elevenlabs-voice-id/versions/latest
      env: ELEVENLABS_VOICE_ID

options:
  logging: CLOUD_LOGGING_ONLY
```

### 5. Dockerfile Optimization

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy worker health script
COPY worker_with_health.py .

# Create startup script
RUN echo '#!/bin/bash\n\
if [ "$SERVICE_TYPE" = "worker" ]; then\n\
    echo "Starting Celery worker..."\n\
    exec python worker_with_health.py\n\
else\n\
    echo "Starting API server..."\n\
    exec gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 8 --timeout 0 app.main:app\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 8080

# Use startup script
CMD ["/app/start.sh"]
```

## Deployment Commands

### 1. Build and Deploy via CLI

```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/storymimi:latest .

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/storymimi:latest

# Deploy API service
gcloud run deploy storymimi-api \
  --image=gcr.io/YOUR_PROJECT_ID/storymimi:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=5 \
  --timeout=300 \
  --vpc-connector=storymimi-connector \
  --update-secrets=REDIS_URL=redis-url:latest \
  --update-env-vars=SERVICE_TYPE=api

# Deploy Worker service
gcloud run deploy storymimi-worker \
  --image=gcr.io/YOUR_PROJECT_ID/storymimi:latest \
  --region=us-central1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=3 \
  --timeout=3600 \
  --cpu-throttling \
  --vpc-connector=storymimi-connector \
  --update-secrets=REDIS_URL=redis-url:latest \
  --update-env-vars=SERVICE_TYPE=worker
```

## Testing and Monitoring

### 1. Test API Endpoint

```bash
# Test story creation
curl -X POST https://storymimi-api-HASH-uc.a.run.app/stories/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Story",
    "prompt": "A magical adventure",
    "user_id": "9a0a594c-2699-400b-89e0-4a4ef78ced97"
  }'
```

### 2. Monitor Logs

```bash
# API logs
gcloud logs tail --follow --filter="resource.type=cloud_run_revision AND resource.labels.service_name=storymimi-api"

# Worker logs
gcloud logs tail --follow --filter="resource.type=cloud_run_revision AND resource.labels.service_name=storymimi-worker"
```

## Key Optimizations for Cloud Run

### 1. Critical Celery Worker Flags
- `--without-mingle`: Prevents startup freeze in Cloud Run
- `--without-gossip`: Reduces network overhead
- `--without-heartbeat`: Prevents heartbeat issues
- `--pool=prefork`: More stable than threads in containers

### 2. Redis Connection Optimization
- Connection retries and timeouts
- Socket keep-alive settings
- Health check intervals
- Proper error handling

### 3. Health Check Implementation
- HTTP endpoint for Cloud Run health checks
- Background daemon thread
- Proper port configuration

### 4. Resource Allocation
- CPU always allocated for worker service
- Appropriate memory and CPU limits
- Timeout settings for long-running tasks

## Troubleshooting

### Common Issues and Solutions

1. **Worker Not Processing Tasks**
   - Check Redis connectivity
   - Verify queue names match
   - Review worker startup logs

2. **Health Check Failures**
   - Ensure health endpoint is accessible
   - Check port configuration
   - Verify daemon thread is running

3. **Redis Connection Drops**
   - Review connection retry settings
   - Check VPC connector configuration
   - Monitor Redis instance health

4. **Task Timeouts**
   - Adjust Cloud Run timeout settings
   - Review task complexity
   - Consider task chunking

## Best Practices

1. **Security**
   - Use Secret Manager for sensitive data
   - Implement proper IAM roles
   - Enable VPC for private communication

2. **Monitoring**
   - Set up Cloud Monitoring alerts
   - Use structured logging
   - Monitor task success rates

3. **Scaling**
   - Configure appropriate min/max instances
   - Set CPU and memory limits
   - Use traffic splitting for testing

4. **Cost Optimization**
   - Use minimum instances carefully
   - Monitor resource usage
   - Implement proper cleanup

## Conclusion

This setup provides a robust foundation for running Celery workers on Cloud Run with Redis. The key is proper configuration of connection handling, health checks, and Cloud Run-specific optimizations.

The solution addresses the main challenges:
- ✅ Redis connection stability
- ✅ Health check requirements
- ✅ Worker scaling
- ✅ Secret management
- ✅ Proper task processing

Regular monitoring and adjustment of configuration parameters will ensure optimal performance in production. 