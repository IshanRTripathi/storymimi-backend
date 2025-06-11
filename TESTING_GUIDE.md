# StoryMimi API Testing Guide

This guide provides detailed instructions for testing the StoryMimi backend API end-to-end, including various methods and tools you can use.

## Prerequisites

1. The StoryMimi backend server is running (using one of the startup methods in the README)
2. The server is accessible at `http://localhost:8000`
3. Mock services are enabled for testing without real API calls (set `USE_MOCK_AI_SERVICES=True` in `.env`)

## Testing Methods

You can test the StoryMimi API using any of the following methods:

1. **Swagger UI**: Interactive web-based API documentation
2. **Postman**: Using the provided collection
3. **Curl Commands**: For command-line testing
4. **Python Requests**: For programmatic testing

## Method 1: Using Swagger UI

Swagger UI provides an interactive interface to test all API endpoints directly in your browser.

1. Start the StoryMimi backend server
2. Open your browser and navigate to `http://localhost:8000/docs`
3. You'll see all available endpoints organized by tags (stories, users)

### Step-by-Step End-to-End Test

1. **Create a User**:
   - Expand the `POST /users/` endpoint
   - Click "Try it out"
   - Enter the request body:
     ```json
     {
       "email": "test@example.com",
       "username": "testuser"
     }
     ```
   - Click "Execute"
   - Copy the `user_id` from the response for later use

2. **Create a Story**:
   - Expand the `POST /stories/` endpoint
   - Click "Try it out"
   - Enter the request body (replace `user_id` with the one from step 1):
     ```json
     {
       "title": "The Magical Forest",
       "prompt": "A child discovers a hidden magical forest behind their house with talking animals and enchanted trees.",
       "style": "fantasy",
       "num_scenes": 3,
       "user_id": "paste-user-id-here"
     }
     ```
   - Click "Execute"
   - Copy the `story_id` from the response for later use

3. **Check Story Status**:
   - Expand the `GET /stories/{story_id}/status` endpoint
   - Click "Try it out"
   - Enter the `story_id` from step 2
   - Click "Execute"
   - The status should initially be `PENDING` or `PROCESSING`
   - Keep checking until the status changes to `COMPLETE` (this may take a few seconds with mock services)

4. **Get Story Details**:
   - Expand the `GET /stories/{story_id}` endpoint
   - Click "Try it out"
   - Enter the `story_id` from step 2
   - Click "Execute"
   - You should see the complete story with all scenes, including text, image URLs, and audio URLs
   - You can copy the image and audio URLs to view/listen to the generated content

5. **Get User Stories**:
   - Expand the `GET /users/{user_id}/stories` endpoint
   - Click "Try it out"
   - Enter the `user_id` from step 1
   - Click "Execute"
   - You should see a list of stories created by the user, including the one you just created

## Method 2: Using Postman

Postman provides a more flexible interface for API testing with the ability to save requests and environments.

1. Import the provided Postman collection:
   - Open Postman
   - Click "Import" > "File" > Select `StoryMimi_Postman_Collection.json`
   - The collection will be imported with all predefined requests

2. Set up environment variables:
   - Create a new environment (e.g., "StoryMimi Local")
   - Add the following variables:
     - `base_url`: `http://localhost:8000`
     - `user_id`: (leave empty for now)
     - `story_id`: (leave empty for now)

3. Follow the same end-to-end testing steps as in the Swagger UI method:
   - Create a user and set the `user_id` environment variable
   - Create a story and set the `story_id` environment variable
   - Check story status until it's complete
   - Get story details
   - Get user stories

## Method 3: Using Curl Commands

For command-line testing, you can use curl commands.

1. **Create a User**:
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/users/' \
     -H 'Content-Type: application/json' \
     -d '{
       "email": "test@example.com",
       "username": "testuser"
     }'
   ```
   Save the `user_id` from the response.

2. **Create a Story**:
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/stories/' \
     -H 'Content-Type: application/json' \
     -d '{
       "title": "The Magical Forest",
       "prompt": "A child discovers a hidden magical forest behind their house with talking animals and enchanted trees.",
       "style": "fantasy",
       "num_scenes": 3,
       "user_id": "paste-user-id-here"
     }'
   ```
   Save the `story_id` from the response.

3. **Check Story Status**:
   ```bash
   curl -X 'GET' \
     'http://localhost:8000/stories/paste-story-id-here/status'
   ```

4. **Get Story Details**:
   ```bash
   curl -X 'GET' \
     'http://localhost:8000/stories/paste-story-id-here'
   ```

5. **Get User Stories**:
   ```bash
   curl -X 'GET' \
     'http://localhost:8000/users/paste-user-id-here/stories'
   ```

## Method 4: Using Python Requests

For programmatic testing, you can use Python with the requests library.

```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Create a user
user_response = requests.post(
    f"{BASE_URL}/users/",
    json={
        "email": "test@example.com",
        "username": "testuser"
    }
)
user_data = user_response.json()
user_id = user_data["user_id"]
print(f"Created user with ID: {user_id}")

# Create a story
story_response = requests.post(
    f"{BASE_URL}/stories/",
    json={
        "title": "The Magical Forest",
        "prompt": "A child discovers a hidden magical forest behind their house with talking animals and enchanted trees.",
        "style": "fantasy",
        "num_scenes": 3,
        "user_id": user_id
    }
)
story_data = story_response.json()
story_id = story_data["story_id"]
print(f"Created story with ID: {story_id}")

# Check story status until complete
while True:
    status_response = requests.get(f"{BASE_URL}/stories/{story_id}/status")
    status_data = status_response.json()
    status = status_data["status"]
    print(f"Story status: {status}")
    
    if status == "COMPLETE":
        break
    elif status == "FAILED":
        print("Story generation failed")
        break
    
    time.sleep(2)  # Wait 2 seconds before checking again

# Get story details
detail_response = requests.get(f"{BASE_URL}/stories/{story_id}")
detail_data = detail_response.json()
print("\nStory Details:")
print(f"Title: {detail_data['title']}")
print(f"Status: {detail_data['status']}")
print(f"Number of scenes: {len(detail_data['scenes'])}")

# Print scene details
for i, scene in enumerate(detail_data["scenes"]):
    print(f"\nScene {i+1}:")
    print(f"Text: {scene['text']}")
    print(f"Image URL: {scene['image_url']}")
    print(f"Audio URL: {scene['audio_url']}")

# Get user stories
user_stories_response = requests.get(f"{BASE_URL}/users/{user_id}/stories")
user_stories_data = user_stories_response.json()
print(f"\nUser has {len(user_stories_data)} stories")
```

## Verifying Media Files

When testing with mock services, you can verify the media files as follows:

1. **Text**: The text content is directly included in the API response

2. **Images**: Copy the image URL from the response and open it in your browser. With mock services, you should see simple colored images (red, blue, or green).

3. **Audio**: Copy the audio URL from the response and open it in your browser or a media player. With mock services, these will be empty MP3 files.

## Troubleshooting

### Common Issues

1. **Server Not Running**:
   - Ensure the server is running using one of the startup methods in the README
   - Check if the server is accessible at `http://localhost:8000/health`

2. **Database Connection Issues**:
   - Verify your Supabase credentials in the `.env` file
   - Check if Supabase is accessible

3. **Redis Connection Issues**:
   - If using Redis, ensure it's running (either via Docker or locally)
   - Check the Redis connection URL in the `.env` file

4. **Story Generation Stuck in PROCESSING**:
   - Check if the Celery worker is running
   - Verify that `USE_MOCK_AI_SERVICES=True` is set in the `.env` file for testing

### Logs

Check the server logs for any error messages or warnings. If running with the startup scripts, the logs will be displayed in the console.

## End-to-End Testing Checklist

Use this checklist to ensure you've tested all aspects of the API:

- [ ] Create a user successfully
- [ ] Create a story with valid parameters
- [ ] Verify story status transitions (PENDING → PROCESSING → COMPLETE)
- [ ] Retrieve complete story details with all scenes
- [ ] Verify text content is generated for each scene
- [ ] Verify image URLs are valid and accessible
- [ ] Verify audio URLs are valid and accessible
- [ ] Retrieve all stories for a user
- [ ] Test error handling (e.g., invalid UUIDs, non-existent resources)

## Next Steps

After successfully testing the API, you can:

1. Integrate with a frontend application
2. Customize the story generation prompts
3. Modify the mock services to return different sample data
4. Switch to real AI services by setting `USE_MOCK_AI_SERVICES=False` and providing valid API keys