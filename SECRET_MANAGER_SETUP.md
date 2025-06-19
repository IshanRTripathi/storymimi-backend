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
- `--command` - For worker: runs Celery worker instead of the default FastAPI server

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
4. **Worker Service**: Deploys `storymimi-worker` as a private Cloud Run service running Celery
5. **Automatic Restart**: Both services restart with new configuration and secrets

## Security Benefits

1. **No Hardcoded Secrets**: API keys are not stored in code or Docker images
2. **Version Control**: Secret Manager maintains version history
3. **Access Control**: Only authorized service accounts can access secrets
4. **Audit Logging**: All secret access is logged
5. **Encryption**: Secrets are encrypted at rest and in transit

## Troubleshooting

### Build Fails with Secret Access Error
1. Verify the secret exists: `gcloud secrets list`
2. Check service account permissions: Cloud Build SA needs `secretmanager.secretAccessor`
3. Verify secret names match exactly in `cloudbuild.yaml`

### Service Deployment Fails
1. Check Cloud Run service has permission to access secrets
2. Verify VPC connector exists: `storymimi-connector`
3. Check logs: `gcloud logging read "resource.type=cloud_run_revision"`

### Missing Environment Variables
1. Verify secrets have values: `gcloud secrets versions list SECRET_NAME`
2. Check service configuration: `gcloud run services describe SERVICE_NAME`

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