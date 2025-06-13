# StoryMimi API Documentation

This document provides detailed information about the StoryMimi backend API endpoints, including request and response formats, examples, and expected behaviors.

## Base URL

All API endpoints are relative to the base URL: `http://localhost:8080`

## Authentication

Currently, the API does not require authentication. User IDs are passed directly in the request body or URL parameters.

## API Endpoints

### Stories API

#### Create a New Story

Generates a new story based on the provided prompt and parameters.

- **URL**: `/stories/`
- **Method**: `POST`
- **Tags**: `stories`

**Request Body**:

```json
{
  "title": "The Magical Forest",
  "prompt": "A child discovers a hidden magical forest behind their house with talking animals and enchanted trees.",
  "style": "fantasy",
  "num_scenes": 3,
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| title | string | Yes | Title of the story |
| prompt | string | Yes | Prompt for story generation |
| style | string | No | Style of the story (e.g., fantasy, sci-fi) |
| num_scenes | integer | No | Number of scenes to generate (default: 3, min: 1, max: 10) |
| user_id | UUID | No | ID of the user requesting the story |

**Response** (Status Code: 202 Accepted):

```json
{
  "story_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "PENDING",
  "created_at": "2023-06-15T10:30:00Z"
}
```

**Error Responses**:

- **500 Internal Server Error**: If story creation fails

#### Get Story Details

Retrieve the full details of a story, including all scenes with text, images, and audio.

- **URL**: `/stories/{story_id}`
- **Method**: `GET`
- **Tags**: `stories`

**Path Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| story_id | UUID | Yes | The ID of the story to retrieve |

**Response** (Status Code: 200 OK):

```json
{
  "story_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "The Magical Forest",
  "status": "COMPLETE",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:35:00Z",
  "scenes": [
    {
      "scene_id": "123e4567-e89b-12d3-a456-426614174001",
      "story_id": "123e4567-e89b-12d3-a456-426614174000",
      "sequence": 0,
      "text": "Once upon a time, a young girl named Lily discovered a hidden path behind her house. The path was overgrown with wildflowers and seemed to shimmer in the sunlight.",
      "image_url": "https://storymimi-storage.supabase.co/storage/v1/object/public/story-images/123e4567-e89b-12d3-a456-426614174001.png",
      "audio_url": "https://storymimi-storage.supabase.co/storage/v1/object/public/story-audio/123e4567-e89b-12d3-a456-426614174001.mp3",
      "created_at": "2023-06-15T10:32:00Z"
    },
    {
      "scene_id": "123e4567-e89b-12d3-a456-426614174002",
      "story_id": "123e4567-e89b-12d3-a456-426614174000",
      "sequence": 1,
      "text": "As Lily followed the path, she entered a magical forest where the trees had faces and whispered secrets to each other. A small rabbit with spectacles approached her.",
      "image_url": "https://storymimi-storage.supabase.co/storage/v1/object/public/story-images/123e4567-e89b-12d3-a456-426614174002.png",
      "audio_url": "https://storymimi-storage.supabase.co/storage/v1/object/public/story-audio/123e4567-e89b-12d3-a456-426614174002.mp3",
      "created_at": "2023-06-15T10:33:00Z"
    },
    {
      "scene_id": "123e4567-e89b-12d3-a456-426614174003",
      "story_id": "123e4567-e89b-12d3-a456-426614174000",
      "sequence": 2,
      "text": "'Welcome to the Whispering Woods,' said the rabbit. 'We've been waiting for someone like you to help us restore the magic that's fading.' Lily's adventure had just begun.",
      "image_url": "https://storymimi-storage.supabase.co/storage/v1/object/public/story-images/123e4567-e89b-12d3-a456-426614174003.png",
      "audio_url": "https://storymimi-storage.supabase.co/storage/v1/object/public/story-audio/123e4567-e89b-12d3-a456-426614174003.mp3",
      "created_at": "2023-06-15T10:34:00Z"
    }
  ]
}
```

**Error Responses**:

- **404 Not Found**: If the story with the specified ID is not found

#### Get Story Status

Check the current status of a story generation process.

- **URL**: `/stories/{story_id}/status`
- **Method**: `GET`
- **Tags**: `stories`

**Path Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| story_id | UUID | Yes | The ID of the story to check |

**Response** (Status Code: 200 OK):

```json
{
  "story_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "PROCESSING"
}
```

**Error Responses**:

- **404 Not Found**: If the story with the specified ID is not found

### Users API

#### Create a New User

Create a new user in the system.

- **URL**: `/users/`
- **Method**: `POST`
- **Tags**: `users`

**Request Body**:

```json
{
  "email": "user@example.com",
  "username": "storywriter"
}
```

**Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| email | string (email) | Yes | User's email address |
| username | string | Yes | User's username |

**Response** (Status Code: 201 Created):

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "username": "storywriter",
  "created_at": "2023-06-15T10:30:00Z"
}
```

**Error Responses**:

- **500 Internal Server Error**: If user creation fails

#### Get User Details

Retrieve details for a specific user.

- **URL**: `/users/{user_id}`
- **Method**: `GET`
- **Tags**: `users`

**Path Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| user_id | UUID | Yes | The ID of the user to retrieve |

**Response** (Status Code: 200 OK):

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "username": "storywriter",
  "created_at": "2023-06-15T10:30:00Z"
}
```

**Error Responses**:

- **404 Not Found**: If the user with the specified ID is not found
- **500 Internal Server Error**: If user retrieval fails

#### Get User Stories

Retrieve all stories created by a specific user.

- **URL**: `/users/{user_id}/stories`
- **Method**: `GET`
- **Tags**: `users`

**Path Parameters**:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| user_id | UUID | Yes | The ID of the user whose stories to retrieve |

**Response** (Status Code: 200 OK):

```json
[
  {
    "story_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "The Magical Forest",
    "status": "COMPLETE",
    "created_at": "2023-06-15T10:30:00Z"
  },
  {
    "story_id": "123e4567-e89b-12d3-a456-426614174001",
    "title": "Space Adventure",
    "status": "PROCESSING",
    "created_at": "2023-06-16T14:20:00Z"
  }
]
```

**Error Responses**:

- **500 Internal Server Error**: If story retrieval fails

## Status Codes

The StoryMimi API uses the following status codes:

- **200 OK**: The request was successful
- **201 Created**: A new resource was successfully created
- **202 Accepted**: The request has been accepted for processing, but processing is not complete
- **400 Bad Request**: The request was invalid or cannot be served
- **404 Not Found**: The requested resource does not exist
- **500 Internal Server Error**: An error occurred on the server

## Story Generation Process

When a story is created through the API, it goes through the following states:

1. **PENDING**: The story has been created and is queued for processing
2. **PROCESSING**: The AI services are generating text, images, and audio for the story
3. **COMPLETE**: All scenes have been generated successfully
4. **FAILED**: An error occurred during the generation process

## Mock Services

When `USE_MOCK_AI_SERVICES=True` is set in the environment, the API will use mock implementations instead of calling real AI services. This is useful for development and testing without consuming API credits.

The mock services return sample data from the `app/mocks/data` directory:
- Text: Sample story texts
- Images: Sample image files
- Audio: Sample audio files

The mock delay can be configured with `MOCK_DELAY_SECONDS` (default: 5.0 seconds).

## Testing the API

You can test the API using the Swagger UI at `http://localhost:8080/docs` or ReDoc at `http://localhost:8080/redoc`.

### Example Workflow

1. Create a user: `POST /users/`
2. Create a story: `POST /stories/`
3. Check the story status: `GET /stories/{story_id}/status`
4. Once the status is `COMPLETE`, get the full story: `GET /stories/{story_id}`
5. View all stories for the user: `GET /users/{user_id}/stories`

## Media Files

The API generates and stores three types of media for each story scene:

1. **Text**: The narrative content of the scene
2. **Images**: Visual representations of the scene (PNG format)
3. **Audio**: Narration of the scene text (MP3 format)

All media files are stored in Supabase Storage and accessible via public URLs returned in the API responses.