#!/bin/bash

# Set variables
REGION=us-central1
PROJECT_ID=$(gcloud config get-value project)
REPO=storymimi-repo
IMAGE_TAG=latest

echo "🚀 Deploying StoryMimi to Cloud Run..."

# 1. Update the API service to use the latest image
echo "📦 Updating API service..."
gcloud run services update storymimi-api \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:$IMAGE_TAG \
  --region=$REGION \
  --quiet

# 2. Update the worker job to use the latest image
echo "🔧 Updating worker job..."
gcloud run jobs update storymimi-worker \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/worker:$IMAGE_TAG \
  --region=$REGION \
  --quiet

echo "✅ Deployment complete!"
echo "🌐 API URL: $(gcloud run services describe storymimi-api --region=$REGION --format='value(status.url)')"
echo "🔧 Worker job: storymimi-worker" 