#!/bin/bash

# Setup Google Cloud Secret Manager secrets for StoryMimi Backend
# This script creates all the required secrets for the application

set -e

echo "🔐 Setting up Google Cloud Secret Manager secrets for StoryMimi..."

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Get current project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project is set. Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Using project: $PROJECT_ID"

# Enable Secret Manager API
echo "🔧 Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_description=$2
    
    echo "🔑 Setting up secret: $secret_name"
    
    # Check if secret exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo "   ✅ Secret $secret_name already exists"
    else
        echo "   ➕ Creating secret $secret_name"
        gcloud secrets create $secret_name \
            --description="$secret_description" \
            --project=$PROJECT_ID
    fi
    
    echo "   📝 Please add the secret value for $secret_name:"
    echo "      gcloud secrets versions add $secret_name --data-file=- --project=$PROJECT_ID"
    echo "      (Then paste your secret value and press Ctrl+D)"
    echo ""
}

# Create all required secrets
echo "📦 Creating secrets..."

create_or_update_secret "REDIS_URL" "Redis connection URL for StoryMimi (e.g., redis://10.x.x.x:6379/0)"
create_or_update_secret "SUPABASE_URL" "Supabase project URL for StoryMimi"
create_or_update_secret "SUPABASE_KEY" "Supabase service role key for StoryMimi"
create_or_update_secret "OPENROUTER_API_KEY" "OpenRouter API key for LLM services"
create_or_update_secret "GEMINI_API_KEY" "Google Gemini API key for LLM services"
create_or_update_secret "TOGETHER_API_KEY" "Together.ai API key for image generation"
create_or_update_secret "ELEVENLABS_API_KEY" "ElevenLabs API key for audio generation"
create_or_update_secret "ELEVENLABS_VOICE_ID" "ElevenLabs voice ID for audio generation"

echo "✅ Secret creation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Add values to each secret using the gcloud commands shown above"
echo "2. Alternatively, you can add values via the Google Cloud Console:"
echo "   https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo ""
echo "3. Grant Cloud Build service account access to secrets:"
echo "   - Go to IAM & Admin > IAM in Google Cloud Console"
echo "   - Find the Cloud Build service account (ends with @cloudbuild.gserviceaccount.com)"
echo "   - Add the 'Secret Manager Secret Accessor' role"
echo ""
echo "4. Your cloudbuild.yaml is now configured to use these secrets!"

# Show how to add secret values
echo ""
echo "🔧 Quick commands to add secret values:"
echo ""
echo "# Redis URL (replace with your actual Redis IP)"
echo "echo 'redis://10.x.x.x:6379/0' | gcloud secrets versions add REDIS_URL --data-file=- --project=$PROJECT_ID"
echo ""
echo "# Supabase URL"
echo "echo 'https://your-project.supabase.co' | gcloud secrets versions add SUPABASE_URL --data-file=- --project=$PROJECT_ID"
echo ""
echo "# Supabase Key"
echo "echo 'your-supabase-service-role-key' | gcloud secrets versions add SUPABASE_KEY --data-file=- --project=$PROJECT_ID"
echo ""
echo "# OpenRouter API Key"
echo "echo 'your-openrouter-api-key' | gcloud secrets versions add OPENROUTER_API_KEY --data-file=- --project=$PROJECT_ID"
echo ""
echo "# Gemini API Key"
echo "echo 'your-gemini-api-key' | gcloud secrets versions add GEMINI_API_KEY --data-file=- --project=$PROJECT_ID"
echo ""
echo "# Together API Key"
echo "echo 'your-together-api-key' | gcloud secrets versions add TOGETHER_API_KEY --data-file=- --project=$PROJECT_ID"
echo ""
echo "# ElevenLabs API Key"
echo "echo 'your-elevenlabs-api-key' | gcloud secrets versions add ELEVENLABS_API_KEY --data-file=- --project=$PROJECT_ID"
echo ""
echo "# ElevenLabs Voice ID"
echo "echo 'your-elevenlabs-voice-id' | gcloud secrets versions add ELEVENLABS_VOICE_ID --data-file=- --project=$PROJECT_ID"
echo ""
echo "🚀 After adding all secrets, commit and push your cloudbuild.yaml changes to trigger a deployment!" 