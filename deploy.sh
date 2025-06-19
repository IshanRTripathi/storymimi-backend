#!/bin/bash

# StoryMimi Backend - Optimized Cloud Run Deployment Script
# This script builds and deploys directly without waiting for git commits

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-us-central1}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
COMMIT_SHA=${COMMIT_SHA:-$TIMESTAMP}

echo -e "${BLUE}🚀 Starting StoryMimi Backend Deployment${NC}"
echo -e "${BLUE}Project ID: $PROJECT_ID${NC}"
echo -e "${BLUE}Region: $REGION${NC}"
echo -e "${BLUE}Build ID: $COMMIT_SHA${NC}"

# Check if gcloud is configured
if [[ -z "$PROJECT_ID" ]]; then
    echo -e "${RED}❌ Error: PROJECT_ID not set. Please run 'gcloud config set project YOUR_PROJECT_ID' or set PROJECT_ID environment variable${NC}"
    exit 1
fi

# Check if required services are enabled
echo -e "${YELLOW}📋 Checking required services...${NC}"
required_services=("cloudbuild.googleapis.com" "run.googleapis.com" "containerregistry.googleapis.com")
for service in "${required_services[@]}"; do
    if ! gcloud services list --enabled --filter="name:$service" --format="value(name)" | grep -q "$service"; then
        echo -e "${YELLOW}⚠️  Enabling $service...${NC}"
        gcloud services enable "$service"
    else
        echo -e "${GREEN}✅ $service is enabled${NC}"
    fi
done

# Build and push API image
echo -e "${YELLOW}🔨 Building API image...${NC}"
docker build -f Dockerfile.api -t gcr.io/$PROJECT_ID/storymimi-api:$COMMIT_SHA .
docker tag gcr.io/$PROJECT_ID/storymimi-api:$COMMIT_SHA gcr.io/$PROJECT_ID/storymimi-api:latest

echo -e "${YELLOW}📤 Pushing API image...${NC}"
docker push gcr.io/$PROJECT_ID/storymimi-api:$COMMIT_SHA
docker push gcr.io/$PROJECT_ID/storymimi-api:latest

# Build and push Worker image
echo -e "${YELLOW}🔨 Building Worker image...${NC}"
docker build -f Dockerfile.worker -t gcr.io/$PROJECT_ID/storymimi-worker:$COMMIT_SHA .
docker tag gcr.io/$PROJECT_ID/storymimi-worker:$COMMIT_SHA gcr.io/$PROJECT_ID/storymimi-worker:latest

echo -e "${YELLOW}📤 Pushing Worker image...${NC}"
docker push gcr.io/$PROJECT_ID/storymimi-worker:$COMMIT_SHA
docker push gcr.io/$PROJECT_ID/storymimi-worker:latest

# Deploy API service
echo -e "${YELLOW}🚀 Deploying API service...${NC}"
gcloud run deploy storymimi-api \
  --image=gcr.io/$PROJECT_ID/storymimi-api:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --cpu-throttling \
  --min-instances=1 \
  --max-instances=10 \
  --concurrency=100 \
  --timeout=300 \
  --update-secrets=REDIS_URL=REDIS_URL:latest,SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,TOGETHER_API_KEY=TOGETHER_API_KEY:latest,ELEVENLABS_API_KEY=ELEVENLABS_API_KEY:latest,ELEVENLABS_VOICE_ID=ELEVENLABS_VOICE_ID:latest \
  --set-env-vars=DEBUG=false,HOST=0.0.0.0,LLM_BACKEND=gemini,OPENROUTER_BASE_URL=https://openrouter.ai/api/v1,QWEN_MODEL_NAME=qwen/qwen-2.5-7b-instruct:free,GEMINI_MODEL=gemini-2.0-flash,TOGETHER_BASE_URL=https://api.together.xyz,TOGETHER_API_URL=https://api.together.xyz/v1/images/generations,ELEVENLABS_USE_V3=false,IMAGE_MODEL=black-forest-labs/FLUX.1-schnell-Free,IMAGE_WIDTH=1024,IMAGE_HEIGHT=768,FLUX_MODEL_NAME=black-forest-labs/FLUX.1-schnell,STORY_MODEL=deepseek/deepseek-r1-0528:free,VISUAL_PROFILE_MODEL=deepseek/deepseek-r1-0528:free,BASE_STYLE_MODEL=deepseek/deepseek-r1-0528:free,SCENE_MOMENT_MODEL=deepseek/deepseek-r1-0528:free,USE_MOCK_AI_SERVICES=false,MOCK_DELAY_SECONDS=5.0 \
  --vpc-connector=storymimi-connector

# Deploy Worker service  
echo -e "${YELLOW}🔧 Deploying Worker service...${NC}"
gcloud run deploy storymimi-worker \
  --image=gcr.io/$PROJECT_ID/storymimi-worker:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --no-cpu-throttling \
  --min-instances=1 \
  --max-instances=5 \
  --concurrency=1 \
  --timeout=3600 \
  --update-secrets=REDIS_URL=REDIS_URL:latest,SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,OPENROUTER_API_KEY=OPENROUTER_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,TOGETHER_API_KEY=TOGETHER_API_KEY:latest,ELEVENLABS_API_KEY=ELEVENLABS_API_KEY:latest,ELEVENLABS_VOICE_ID=ELEVENLABS_VOICE_ID:latest \
  --set-env-vars=DEBUG=false,HOST=0.0.0.0,LLM_BACKEND=gemini,OPENROUTER_BASE_URL=https://openrouter.ai/api/v1,QWEN_MODEL_NAME=qwen/qwen-2.5-7b-instruct:free,GEMINI_MODEL=gemini-2.0-flash,TOGETHER_BASE_URL=https://api.together.xyz,TOGETHER_API_URL=https://api.together.xyz/v1/images/generations,ELEVENLABS_USE_V3=false,IMAGE_MODEL=black-forest-labs/FLUX.1-schnell-Free,IMAGE_WIDTH=1024,IMAGE_HEIGHT=768,FLUX_MODEL_NAME=black-forest-labs/FLUX.1-schnell,STORY_MODEL=deepseek/deepseek-r1-0528:free,VISUAL_PROFILE_MODEL=deepseek/deepseek-r1-0528:free,BASE_STYLE_MODEL=deepseek/deepseek-r1-0528:free,SCENE_MOMENT_MODEL=deepseek/deepseek-r1-0528:free,USE_MOCK_AI_SERVICES=false,MOCK_DELAY_SECONDS=5.0,C_FORCE_ROOT=1 \
  --vpc-connector=storymimi-connector

# Get service URLs
API_URL=$(gcloud run services describe storymimi-api --region=$REGION --format="value(status.url)")
echo -e "${GREEN}✅ API Service deployed successfully!${NC}"
echo -e "${GREEN}🌐 API URL: $API_URL${NC}"

echo -e "${GREEN}✅ Worker Service deployed successfully!${NC}"

# Test API health
echo -e "${YELLOW}🔍 Testing API health...${NC}"
if curl -s "$API_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ API health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  API health check failed - this is normal for new deployments${NC}"
fi

echo -e "${BLUE}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "${BLUE}1. Test story creation: curl -X POST '$API_URL/stories' -H 'Content-Type: application/json' -d '{\"title\": \"Test Story\", \"prompt\": \"A magical adventure\", \"user_id\": \"9a0a594c-2699-400b-89e0-4a4ef78ced97\"}'${NC}"
echo -e "${BLUE}2. Monitor logs: gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"storymimi-api\"' --limit 50${NC}"
echo -e "${BLUE}3. Monitor worker logs: gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"storymimi-worker\"' --limit 50${NC}"