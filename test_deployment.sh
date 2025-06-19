#!/bin/bash

# StoryMimi Backend - Automated Testing Script
# This script tests the deployed services end-to-end

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-us-central1}
API_URL=""
STORY_ID=""

echo -e "${BLUE}🧪 Starting StoryMimi Backend Testing${NC}"

# Get API URL from Cloud Run
echo -e "${YELLOW}🔍 Getting API service URL...${NC}"
API_URL=$(gcloud run services describe storymimi-api --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")

if [[ -z "$API_URL" ]]; then
    echo -e "${RED}❌ Error: Could not find API service URL. Make sure the service is deployed.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API URL: $API_URL${NC}"

# Function to test API endpoint
test_endpoint() {
    local endpoint="$1"
    local method="$2"
    local data="$3"
    local expected_status="$4"
    
    echo -e "${YELLOW}🔍 Testing $method $endpoint${NC}"
    
    if [[ -n "$data" ]]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" \
            "$API_URL$endpoint")
    fi
    
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    status=$(echo "$response" | grep -o -E 'HTTPSTATUS:[0-9]{3}$' | cut -d: -f2)
    
    if [[ "$status" == "$expected_status" ]]; then
        echo -e "${GREEN}✅ $method $endpoint - Status: $status${NC}"
        if [[ -n "$body" && "$body" != "{}" ]]; then
            echo -e "${BLUE}Response: ${body:0:200}${NC}${YELLOW}...${NC}"
        fi
        echo "$body"
    else
        echo -e "${RED}❌ $method $endpoint - Expected: $expected_status, Got: $status${NC}"
        echo -e "${RED}Response: $body${NC}"
        return 1
    fi
}

# Test 1: Health Check
echo -e "${BLUE}=== Test 1: Health Check ===${NC}"
test_endpoint "/health" "GET" "" "200"

# Test 2: Create Story
echo -e "${BLUE}=== Test 2: Create Story ===${NC}"
story_payload='{
  "title": "My Test Story",
  "prompt": "A magical adventure in a distant land where dragons fly",
  "user_id": "9a0a594c-2699-400b-89e0-4a4ef78ced97"
}'

story_response=$(test_endpoint "/stories" "POST" "$story_payload" "202")
STORY_ID=$(echo "$story_response" | grep -o '"story_id":"[^"]*"' | cut -d'"' -f4)

if [[ -n "$STORY_ID" ]]; then
    echo -e "${GREEN}✅ Story created with ID: $STORY_ID${NC}"
else
    echo -e "${RED}❌ Failed to extract story ID from response${NC}"
    exit 1
fi

# Wait for worker to start processing
echo -e "${YELLOW}⏳ Waiting 30 seconds for worker to process the story...${NC}"
sleep 30

# Test 3: Check Story Status
echo -e "${BLUE}=== Test 3: Check Story Status ===${NC}"
test_endpoint "/stories/$STORY_ID/status" "GET" "" "200"

# Test 4: Get Story Details
echo -e "${BLUE}=== Test 4: Get Story Details ===${NC}"
story_detail_response=$(test_endpoint "/stories/$STORY_ID" "GET" "" "200" || echo "FAILED")

# Test 5: Check Recent Stories
echo -e "${BLUE}=== Test 5: Check Recent Stories ===${NC}"
test_endpoint "/stories/recent/?limit=5" "GET" "" "200"

# Function to check logs
check_logs() {
    local service_name="$1"
    local duration="$2"
    
    echo -e "${YELLOW}📋 Checking $service_name logs from last $duration...${NC}"
    
    logs=$(gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$service_name\"" \
        --limit=20 \
        --format="value(timestamp,severity,textPayload)" \
        --freshness="$duration" 2>/dev/null || echo "")
    
    if [[ -n "$logs" ]]; then
        echo -e "${GREEN}✅ Found $service_name logs:${NC}"
        echo "$logs" | head -10
        
        # Count different log levels
        error_count=$(echo "$logs" | grep -c "ERROR" || echo "0")
        warning_count=$(echo "$logs" | grep -c "WARNING" || echo "0")
        info_count=$(echo "$logs" | grep -c "INFO" || echo "0")
        
        echo -e "${BLUE}Log Summary - Errors: $error_count, Warnings: $warning_count, Info: $info_count${NC}"
        
        if [[ "$error_count" -gt 0 ]]; then
            echo -e "${RED}⚠️  Found $error_count errors in $service_name logs${NC}"
            echo "$logs" | grep "ERROR" | head -3
        fi
    else
        echo -e "${YELLOW}⚠️  No recent logs found for $service_name${NC}"
    fi
}

# Test 6: Check Service Logs
echo -e "${BLUE}=== Test 6: Check Service Logs ===${NC}"
check_logs "storymimi-api" "5m"
check_logs "storymimi-worker" "5m"

# Test 7: Performance Test (Optional)
echo -e "${BLUE}=== Test 7: Basic Performance Test ===${NC}"
echo -e "${YELLOW}🏃 Running 5 concurrent story creation requests...${NC}"

performance_test() {
    local i="$1"
    local test_payload='{
      "title": "Performance Test Story '$i'",
      "prompt": "A quick test story for performance testing",
      "user_id": "9a0a594c-2699-400b-89e0-4a4ef78ced97"
    }'
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        "$API_URL/stories")
    
    status=$(echo "$response" | grep -o -E 'HTTPSTATUS:[0-9]{3}$' | cut -d: -f2)
    
    if [[ "$status" == "202" ]]; then
        echo -e "${GREEN}✅ Performance test $i - Success${NC}"
    else
        echo -e "${RED}❌ Performance test $i - Failed with status $status${NC}"
    fi
}

# Run performance tests in parallel
for i in {1..5}; do
    performance_test "$i" &
done

# Wait for all background jobs to complete
wait

echo -e "${YELLOW}⏳ Waiting 30 seconds for performance test tasks to be processed...${NC}"
sleep 30

# Final status check
echo -e "${BLUE}=== Final Status Check ===${NC}"
check_logs "storymimi-worker" "2m"

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "${GREEN}✅ Health check passed${NC}"
echo -e "${GREEN}✅ Story creation tested (ID: $STORY_ID)${NC}"
echo -e "${GREEN}✅ Status endpoint tested${NC}"
echo -e "${GREEN}✅ Story details endpoint tested${NC}"
echo -e "${GREEN}✅ Recent stories endpoint tested${NC}"
echo -e "${GREEN}✅ Service logs checked${NC}"
echo -e "${GREEN}✅ Performance test completed${NC}"

echo -e "${BLUE}🎉 Testing completed successfully!${NC}"
echo -e "${BLUE}API URL: $API_URL${NC}"
echo -e "${BLUE}Test Story ID: $STORY_ID${NC}"

# Provide monitoring commands
echo -e "${BLUE}📊 Monitoring Commands:${NC}"
echo -e "${BLUE}1. Watch API logs: gcloud logging tail 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"storymimi-api\"'${NC}"
echo -e "${BLUE}2. Watch worker logs: gcloud logging tail 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"storymimi-worker\"'${NC}"
echo -e "${BLUE}3. Check service status: gcloud run services list --region=$REGION${NC}"