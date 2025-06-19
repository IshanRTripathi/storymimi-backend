# Supabase Client Import Mapping

This document provides a comprehensive guide for importing and using database operations from the modularized Supabase client.

## Import Structure

### Base Import
```python
from app.database.supabase_client import SupabaseBaseClient
```

### Domain-Specific Imports
```python
from app.database.supabase_client import (
    UserRepository,     # User-related operations
    StoryRepository,    # Story-related operations
    SceneRepository,    # Scene-related operations
    StorageService,     # File storage operations
    SupabaseHealthService,  # Health check operations
)
```

## File Structure and Usage

### Base Client
- `base_client.py`: Contains the base client class and common utilities
- Common imports:
  ```python
  from app.database.supabase_client.base_client import SupabaseBaseClient
  ```
- Usage:
  ```python
  base_client = SupabaseBaseClient()
  # Access common utilities through base_client
  ```

### User Operations
- `users_db_client.py`: Handles user-related database operations
- Available operations:
  - `create_user`: Create a new user
  - `get_user`: Retrieve a user by ID
  - `update_user`: Update user information
  - `delete_user`: Delete a user
  - `get_users`: List users with pagination
- Usage example:
  ```python
  from app.database.supabase_client.users_db_client import UserRepository

  user_repo = UserRepository()
  user = await user_repo.create_user(email="test@example.com", username="testuser")
  ```

### Story Operations
- `stories_db_client.py`: Manages story-related database operations
- Available operations:
  - `create_story`: Create a new story
  - `get_story`: Retrieve a story by ID
  - `update_story`: Update story information
  - `update_story_status`: Change story status
  - `delete_story`: Delete a story
  - `count_stories`: Count stories (with optional status filter)
  - `search_stories`: Search stories by title or prompt
  - `get_recent_stories`: Get recently created stories
  - `get_user_story_count`: Count stories for a user
- Usage example:
  ```python
  from app.database.supabase_client.stories_db_client import StoryRepository

  story_repo = StoryRepository()
  story = await story_repo.create_story(title="My Story", prompt="Write about...", user_id="user-id")
  ```

### Scene Operations
- `scenes_db_client.py`: Handles scene-related database operations
- Available operations:
  - `create_scene`: Create a new scene
  - `get_scene`: Retrieve a scene by ID
  - `get_story_scenes`: Get all scenes for a story
  - `delete_scene`: Delete a scene
  - `batch_insert_scenes`: Insert multiple scenes at once
- Usage example:
  ```python
  from app.database.supabase_client.scenes_db_client import SceneRepository

  scene_repo = SceneRepository()
  scene = await scene_repo.create_scene(
      story_id="story-id",
      sequence=1,
      text="Scene text",
      image_url="image-url",
      audio_url="audio-url"
  )
  ```

### Storage Operations
- `storage_db_client.py`: Manages file storage operations
- Available operations:
  - `upload_image`: Upload image files
  - `upload_audio`: Upload audio files
  - `delete_file`: Delete a file from storage
  - `delete_story_files`: Delete all files associated with a story
  - `list_bucket_files`: List files in a bucket
- Usage example:
  ```python
  from app.database.supabase_client.storage_db_client import StorageService

  storage_service = StorageService()
  image_url = await storage_service.upload_image(
      story_id="story-id",
      scene_sequence=1,
      image_bytes=image_data
  )
  ```

### Health Checks
- `health_db_client.py`: Contains health check functionality
- Available operations:
  - `check_connection`: Verify Supabase connection
- Usage example:
  ```python
  from app.database.supabase_client.health_db_client import SupabaseHealthService

  health_service = SupabaseHealthService()
  is_connected = await health_service.check_connection()
  ```

## Error Handling

Each service inherits from `SupabaseBaseClient` which provides:
- Common error handling
- Logging utilities
- Connection management

```python
try:
    # Perform operation
    result = await service.some_operation()
except Exception as e:
    # Handle error
    logger.error(f"Operation failed: {str(e)}")
```

## Best Practices

1. Import only the services you need
2. Create service instances at the appropriate scope (e.g., class level for a service class)
3. Handle errors at the application level
4. Use async/await for all operations
5. Clean up resources (like BytesIO) when using storage operations

## Import Scenarios

### Single Service Import
```python
# Importing just the user repository
from app.database.supabase_client.users_db_client import UserRepository
```

### Multiple Services Import
```python
# Importing multiple services
from app.database.supabase_client import (
    UserRepository,
    StoryRepository,
    SceneRepository
)
```

### Using Services Together
```python
# Example of using multiple services together
async def create_story_with_scene(user_id: str, title: str, prompt: str):
    # Initialize repositories
    user_repo = UserRepository()
    story_repo = StoryRepository()
    scene_repo = SceneRepository()
    
    try:
        # Create story
        story = await story_repo.create_story(title, prompt, user_id)
        
        # Create first scene
        scene = await scene_repo.create_scene(
            story_id=story["story_id"],
            sequence=1,
            text="First scene",
            image_url="",
            audio_url=""
        )
        
        return story, scene
        
    except Exception as e:
        logger.error(f"Failed to create story and scene: {str(e)}")
        raise
```

## User Operations

### UserRepository
- `create_user`: Create a new user
- `get_user`: Retrieve a user by ID
- `update_user`: Update user information
- `delete_user`: Delete a user
- `get_users`: List users with pagination

```python
from app.database.supabase_client import UserRepository

# Usage example
user_repo = UserRepository()
user = await user_repo.create_user(email="test@example.com", username="testuser")
```

## Story Operations

### StoryRepository
- `create_story`: Create a new story
- `get_story`: Retrieve a story by ID
- `update_story`: Update story information
- `update_story_status`: Change story status
- `delete_story`: Delete a story
- `count_stories`: Count stories (with optional status filter)
- `search_stories`: Search stories by title or prompt
- `get_recent_stories`: Get recently created stories
- `get_user_story_count`: Count stories for a user

```python
from app.database.supabase_client import StoryRepository

# Usage example
story_repo = StoryRepository()
story = await story_repo.create_story(title="My Story", prompt="Write about...", user_id="user-id")
```

## Scene Operations

### SceneRepository
- `create_scene`: Create a new scene
- `get_scene`: Retrieve a scene by ID
- `get_story_scenes`: Get all scenes for a story
- `delete_scene`: Delete a scene
- `batch_insert_scenes`: Insert multiple scenes at once

```python
from app.database.supabase_client import SceneRepository

# Usage example
scene_repo = SceneRepository()
scene = await scene_repo.create_scene(
    story_id="story-id",
    sequence=1,
    text="Scene text",
    image_url="image-url",
    audio_url="audio-url"
)
```

## Storage Operations

### StorageService
- `upload_image`: Upload image files
- `upload_audio`: Upload audio files
- `delete_file`: Delete a file from storage
- `delete_story_files`: Delete all files associated with a story
- `list_bucket_files`: List files in a bucket

```python
from app.database.supabase_client import StorageService

# Usage example
storage_service = StorageService()
image_url = await storage_service.upload_image(
    story_id="story-id",
    scene_sequence=1,
    image_bytes=image_data
)
```

## Health Checks

### SupabaseHealthService
- `check_connection`: Verify Supabase connection

```python
from app.database.supabase_client import SupabaseHealthService

# Usage example
health_service = SupabaseHealthService()
is_connected = await health_service.check_connection()
```

## Error Handling

Each service inherits from `SupabaseBaseClient` which provides:
- Common error handling
- Logging utilities
- Connection management

```python
try:
    # Perform operation
    result = await service.some_operation()
except Exception as e:
    # Handle error
    logger.error(f"Operation failed: {str(e)}")
```

## Best Practices

1. Import only the services you need
2. Create service instances at the appropriate scope (e.g., class level for a service class)
3. Handle errors at the application level
4. Use async/await for all operations
5. Clean up resources (like BytesIO) when using storage operations
