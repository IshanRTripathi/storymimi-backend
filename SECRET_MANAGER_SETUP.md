# Secret Manager Configuration for StoryMimi Backend

This document explains how the StoryMimi backend is configured to use Google Cloud Secret Manager for storing sensitive API keys and configuration values.

## Overview

The `cloudbuild.yaml` file has been configured to:
1. Access secrets from Google Cloud Secret Manager during the build process
2. Deploy both API and worker services with proper secret configuration
3. Separate sensitive data (API keys) from non-sensitive configuration (URLs, model names)

## Configured Secrets

The following secrets are configured in Secret Manager:

### Required Secrets
- `REDIS_URL` - Redis connection URL (e.g., `redis://10.x.x.x:6379/0`)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM services
- `GEMINI_API_KEY` - Google Gemini API key for LLM services
- `TOGETHER_API_KEY` - Together.ai API key for image generation
- `ELEVENLABS_API_KEY` - ElevenLabs API key for audio generation
- `ELEVENLABS_VOICE_ID` - ElevenLabs voice ID for audio generation

### Existing Secrets (Already Created)
✅ All secrets have been created in your GCP project.

## Cloud Build Configuration

### Secret Access
The `cloudbuild.yaml` includes:
```yaml
availableSecrets:
  secretManager:
  - versionName: projects/$PROJECT_ID/secrets/REDIS_URL/versions/latest
    env: 'REDIS_URL'
  # ... other secrets
```

### Service Deployment
Both API and worker services are deployed as Cloud Run services with:
- `secretEnv` - Makes secrets available to the build step
- `--update-secrets` - Configures Cloud Run services to access secrets
- `--set-env-vars` - Sets non-sensitive environment variables
- `--command` - For worker: runs `worker_with_health.py` (Celery + HTTP health endpoint)

## Permissions

The Cloud Build service account has been granted the `roles/secretmanager.secretAccessor` role to access secrets during the build process.

## Environment Variables

### Secrets (from Secret Manager)
- Database: `SUPABASE_URL`, `SUPABASE_KEY`
- Cache: `REDIS_URL`
- AI Services: `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `TOGETHER_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`

### Non-Sensitive Configuration (set directly)
- Application: `DEBUG=false`, `HOST=0.0.0.0`, `PORT=8080`
- LLM Backend: `LLM_BACKEND=gemini`
- API URLs: `OPENROUTER_BASE_URL`, `TOGETHER_BASE_URL`, `TOGETHER_API_URL`
- Model Names: `QWEN_MODEL_NAME`, `GEMINI_MODEL`, `FLUX_MODEL_NAME`, etc.
- Feature Flags: `ELEVENLABS_USE_V3=false`, `USE_MOCK_AI_SERVICES=false`

## Adding or Updating Secret Values

### Via Command Line
```bash
# Add a new secret value
echo 'your-secret-value' | gcloud secrets versions add SECRET_NAME --data-file=-

# Examples:
echo 'redis://10.1.2.3:6379/0' | gcloud secrets versions add REDIS_URL --data-file=-
echo 'your-openrouter-key' | gcloud secrets versions add OPENROUTER_API_KEY --data-file=-
```

### Via Google Cloud Console
1. Go to [Secret Manager](https://console.cloud.google.com/security/secret-manager)
2. Click on the secret name
3. Click "ADD NEW VERSION"
4. Paste your secret value
5. Click "ADD NEW VERSION"

## Deployment Process

1. **Build Trigger**: Push to GitHub triggers Cloud Build
2. **Secret Access**: Cloud Build accesses secrets during deployment
3. **API Service**: Deploys `storymimi-api` as a public Cloud Run service
4. **Worker Service**: Deploys `storymimi-worker` as a private Cloud Run service running Celery with HTTP health checks
5. **Automatic Restart**: Both services restart with new configuration and secrets

## Worker Health Check Solution

The Celery worker runs with a custom script (`worker_with_health.py`) that:
- **Dual Purpose**: Runs both Celery worker and HTTP health check server
- **Health Endpoint**: Provides `/health` endpoint on port 8080 for Cloud Run probes
- **Background Threading**: Health server runs in daemon thread, Celery in main thread
- **Cloud Run Compatible**: Satisfies Cloud Run's requirement for HTTP health checks

This solves the issue where Cloud Run expects HTTP responses but Celery workers don't provide them.

## Security Benefits

1. **No Hardcoded Secrets**: API keys are not stored in code or Docker images
2. **Version Control**: Secret Manager maintains version history
3. **Access Control**: Only authorized service accounts can access secrets
4. **Audit Logging**: All secret access is logged
5. **Encryption**: Secrets are encrypted at rest and in transit

## Troubleshooting

### Celery 5.x Redis Reconnection Bug - CRITICAL FIX

**Problem**: This is a well-known bug in Celery 5.x where workers stop consuming tasks after Redis reconnection. Symptoms include:
```
Connection to Redis lost: Retry (6/20) in 1.00 second.
worker: Warm shutdown (MainProcess)
```
After Redis reconnection, workers appear healthy but stop processing tasks indefinitely.

**Root Cause**: 
- Bug in Celery 5.x mingle/gossip/heartbeat mechanism with Redis
- Worker gets stuck after Redis connection drops and reconnects
- Affects all Celery 5.x versions with Redis broker

**Solution Implemented**: Multi-layered fix addressing all aspects of the bug:

#### 1. Worker Command Line Flags (MOST CRITICAL)
```bash
celery worker \
  --without-mingle \      # CRITICAL: Prevents reconnection freeze
  --without-gossip \      # CRITICAL: Prevents reconnection freeze  
  --without-heartbeat \   # CRITICAL: Prevents heartbeat issues
  --pool=prefork \        # Better stability
  --optimization=fair     # Fair task distribution
```

#### 2. Enhanced Redis Connection Configuration
```python
broker_transport_options={
    'visibility_timeout': 7200,        # 2 hours (longer than task timeout)
    'socket_timeout': 120.0,           # 2 minutes socket timeout
    'socket_connect_timeout': 30.0,    # 30 seconds connect timeout
    'socket_keepalive': True,
    'socket_keepalive_options': {
        'TCP_KEEPINTVL': 10,           # Keepalive probe interval
        'TCP_KEEPCNT': 6,              # Max keepalive probes
        'TCP_KEEPIDLE': 60,            # Idle time before keepalive
    },
    'health_check_interval': 25,       # Health check frequency
    'max_connections': 20,             # Connection pool size
}
```

#### 3. Connection Retry Settings
```python
broker_connection_retry=True,
broker_connection_max_retries=None,   # Retry indefinitely
broker_connection_retry_delay=5.0,    # 5 second delay between retries
```

#### 4. Task Reliability Settings
```python
task_acks_late=True,                  # Acknowledge after completion
worker_prefetch_multiplier=1,         # One task per worker
task_reject_on_worker_lost=True,      # Reject tasks if worker lost
worker_cancel_long_running_tasks_on_connection_loss=True,
```

**References**: 
- [Celery GitHub Issue #7276](https://github.com/celery/celery/discussions/7276)
- Affects: Celery 5.0+, Redis broker, all deployment environments
- Status: Fixed in our implementation, monitoring for Celery 5.4+ official fix

**Verification**: 
- Monitor worker logs for task processing after Redis restarts
- Check that tasks are consumed within expected timeframes
- Verify no "warm shutdown" messages after Redis reconnections

### Redis Connection Issues

**Problem**: Redis connection timeouts, lack of connection pooling, and inadequate retry logic.

**Solution**: Enhanced Celery configuration with:
- **Connection Retry**: `broker_connection_retry=True` with indefinite retries
- **Socket Keep-Alive**: TCP keep-alive options for persistent connections
- **Connection Pooling**: Limited pool size to prevent connection exhaustion
- **Task Acknowledgment**: Late acknowledgment (`task_acks_late=True`) for reliability
- **Worker Options**: `--without-gossip --without-mingle --without-heartbeat` for stability

### Build and Deployment Issues

**Problem**: Cloud Build failures, missing files, or service deployment errors.

**Solution**: 
- Verify all required files are copied in Dockerfile
- Check Cloud Build service account permissions
- Ensure Secret Manager secrets are properly configured
- Validate VPC connector and Redis connectivity

### Health Check Failures

**Problem**: Cloud Run health checks failing for worker service.

**Solution**: 
- Worker includes HTTP health check server on port 8080
- Health endpoint responds at `/health` and `/`
- Daemon thread runs health server alongside Celery worker

## Next Steps

1. **Add Secret Values**: Use the commands above to add actual API keys
2. **Monitor Deployments**: Check Cloud Build logs for any issues
3. **Test Services**: Verify both API and worker can access secrets
4. **Update as Needed**: Add new secrets or update existing ones as required

## Security Recommendations

1. **Rotate Keys Regularly**: Update API keys periodically
2. **Monitor Access**: Review Secret Manager audit logs
3. **Least Privilege**: Only grant necessary permissions
4. **Backup Secrets**: Keep secure backups of critical API keys
5. **Environment Separation**: Use different secrets for dev/staging/prod 

## Maintenance

### Updating Secret Values
```bash
# Update a secret value
echo 'new-secret-value' | gcloud secrets versions add SECRET_NAME --data-file=-

# List secret versions
gcloud secrets versions list SECRET_NAME

# Access specific version
gcloud secrets versions access VERSION_NUMBER --secret=SECRET_NAME
```

### Monitoring
- Monitor Cloud Build logs for deployment issues
- Check Cloud Run logs for runtime errors
- Use Cloud Logging to track secret access patterns
- Set up alerts for failed deployments or service errors 