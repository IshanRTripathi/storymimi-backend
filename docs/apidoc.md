# StoryMimi Supabase Client Reference

This document provides a comprehensive reference for Supabase operations used in the StoryMimi backend, including detailed examples of CRUD operations, storage management, and best practices for error handling and logging.

## Database Schema

The StoryMimi application uses the following tables:

### Users Table
```json
{
  "user_id": "uuid",         // Primary key, UUID string
  "username": "string",     // User's display name
  "email": "string",       // User's email address
  "created_at": "timestamp" // Automatically managed by Supabase
}
```

### Stories Table
```json
{
  "story_id": "uuid",       // Primary key, UUID string
  "user_id": "uuid",        // Foreign key to users table
  "title": "string",       // Story title
  "prompt": "string",      // Original prompt for story generation
  "status": "string",      // Current status (PENDING, GENERATING, COMPLETED, ERROR)
  "created_at": "timestamp", // Automatically managed by Supabase
  "updated_at": "timestamp"  // Automatically managed by Supabase
}
```

### Scenes Table
```json
{
  "scene_id": "uuid",       // Primary key, UUID string
  "story_id": "uuid",      // Foreign key to stories table
  "sequence": "integer",   // Order of scene in story
  "text": "string",        // Scene text content
  "image_url": "string",   // URL to scene image
  "audio_url": "string",   // URL to scene audio narration
  "created_at": "timestamp" // Automatically managed by Supabase
}
```

## Client Initialization with Logging

```python
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
import uuid
import io
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

# Configure logger
logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self, url: str, key: str):
        logger.info(f"Initializing Supabase client with URL: {url}")
        start_time = time.time()
        
        try:
            # Configure client options for better reliability
            options = ClientOptions(
                schema="public",
                headers={"x-client-info": "storymimi-backend"},
                auto_refresh_token=True,
                persist_session=False,
                timeout=15  # 15 seconds timeout for requests
            )
            
            # Create the client
            self.client = create_client(url, key, options=options)
            
            elapsed = time.time() - start_time
            logger.info(f"Supabase client initialized successfully in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to initialize Supabase client in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
```

## CRUD Operations with Error Handling and Logging

### User Operations

#### Create a User

```python
async def create_user(self, email: str, username: str) -> Dict[str, Any]:
    start_time = time.time()
    user_id = str(uuid.uuid4())
    user_data = {
        "email": email,
        "username": username,
        "user_id": user_id
    }
    
    logger.info(f"Creating new user with email: {email}, username: {username}, user_id: {user_id}")
    self._log_operation("insert", "users", user_data)
    
    try:
        response = self.client.table("users").insert(user_data).execute()
        
        if not response.data:
            logger.error(f"Failed to create user: No data returned from database")
            return None
            
        elapsed = time.time() - start_time
        logger.info(f"User created successfully in {elapsed:.2f}s: {user_id}")
        return response.data[0]
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to create user in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Get a User

```python
async def get_user(self, user_id: str) -> Dict[str, Any]:
    start_time = time.time()
    user_id_str = str(user_id)
    
    logger.info(f"Getting user with ID: {user_id_str}")
    self._log_operation("select", "users", filters={"user_id": user_id_str})
    
    try:
        response = self.client.table("users").select("*").eq("user_id", user_id_str).execute()
        
        if not response.data:
            logger.warning(f"User not found with ID: {user_id_str}")
            return None
            
        elapsed = time.time() - start_time
        logger.info(f"User retrieved successfully in {elapsed:.2f}s: {user_id_str}")
        return response.data[0]
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to get user in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Update a User

```python
async def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.time()
    user_id_str = str(user_id)
    
    logger.info(f"Updating user with ID: {user_id_str}, fields: {list(data.keys())}")
    self._log_operation("update", "users", data, {"user_id": user_id_str})
    
    try:
        response = self.client.table("users").update(data).eq("user_id", user_id_str).execute()
        
        if not response.data:
            logger.warning(f"User update failed, no data returned: {user_id_str}")
            return None
            
        elapsed = time.time() - start_time
        logger.info(f"User updated successfully in {elapsed:.2f}s: {user_id_str}")
        return response.data[0]
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to update user in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Delete a User

```python
async def delete_user(self, user_id: str) -> bool:
    start_time = time.time()
    user_id_str = str(user_id)
    
    logger.info(f"Deleting user with ID: {user_id_str}")
    self._log_operation("delete", "users", filters={"user_id": user_id_str})
    
    try:
        response = self.client.table("users").delete().eq("user_id", user_id_str).execute()
        success = bool(response.data)
        
        elapsed = time.time() - start_time
        if success:
            logger.info(f"User deleted successfully in {elapsed:.2f}s: {user_id_str}")
        else:
            logger.warning(f"User deletion returned no data in {elapsed:.2f}s: {user_id_str}")
            
        return success
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to delete user in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Get All Users (Paginated)

```python
async def get_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    start_time = time.time()
    
    logger.info(f"Getting users with limit: {limit}, offset: {offset}")
    self._log_operation("select", "users", filters={"limit": limit, "offset": offset})
    
    try:
        response = self.client.table("users").select("*").range(offset, offset + limit - 1).execute()
        users = response.data if response.data else []
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(users)} users successfully in {elapsed:.2f}s")
        return users
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to get users in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Story Operations

#### Create a Story

```python
async def create_story(self, title: str, prompt: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    start_time = time.time()
    story_id = uuid.uuid4()
    story_id_str = str(story_id)
    user_id_str = str(user_id) if user_id else None
    
    story_data = {
        "story_id": story_id_str,
        "title": title,
        "prompt": prompt,
        "status": "PENDING",  # Using enum value
        "user_id": user_id_str
    }
    
    logger.info(f"Creating new story with ID: {story_id_str}, title: {title}, user_id: {user_id_str}")
    self._log_operation("insert", "stories", story_data)
    
    try:
        response = self.client.table("stories").insert(story_data).execute()
        
        if not response.data:
            logger.error(f"Failed to create story: No data returned from database")
            return None
            
        elapsed = time.time() - start_time
        logger.info(f"Story created successfully in {elapsed:.2f}s: {story_id_str}")
        return response.data[0]
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to create story in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Get a Story

```python
async def get_story(self, story_id: str) -> Dict[str, Any]:
    start_time = time.time()
    story_id_str = str(story_id)
    
    logger.info(f"Getting story with ID: {story_id_str}")
    self._log_operation("select", "stories", filters={"story_id": story_id_str})
    
    try:
        response = self.client.table("stories").select("*").eq("story_id", story_id_str).execute()
        
        if not response.data:
            logger.warning(f"Story not found with ID: {story_id_str}")
            return None
            
        elapsed = time.time() - start_time
        logger.info(f"Story retrieved successfully in {elapsed:.2f}s: {story_id_str}")
        return response.data[0]
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to get story in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Update Story Status

```python
async def update_story_status(self, story_id: str, status: str) -> bool:
    start_time = time.time()
    story_id_str = str(story_id)
    
    logger.info(f"Updating story status for ID: {story_id_str} to {status}")
    self._log_operation("update", "stories", {"status": status}, {"story_id": story_id_str})
    
    try:
        response = self.client.table("stories").update({"status": status}).eq("story_id", story_id_str).execute()
        success = bool(response.data)
        
        elapsed = time.time() - start_time
        if success:
            logger.info(f"Story status updated successfully in {elapsed:.2f}s: {story_id_str} -> {status}")
        else:
            logger.warning(f"Story status update returned no data in {elapsed:.2f}s: {story_id_str}")
            
        return success
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to update story status in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Get User Stories

```python
async def get_user_stories(self, user_id: str) -> List[Dict[str, Any]]:
    start_time = time.time()
    user_id_str = str(user_id)
    
    logger.info(f"Getting stories for user ID: {user_id_str}")
    self._log_operation("select", "stories", filters={"user_id": user_id_str})
    
    try:
        response = self.client.table("stories").select("*").eq("user_id", user_id_str).order("created_at", desc=True).execute()
        stories = response.data if response.data else []
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(stories)} stories successfully in {elapsed:.2f}s for user: {user_id_str}")
        return stories
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to get user stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Scene Operations

#### Create a Scene

```python
async def create_scene(self, story_id: str, sequence: int, text: str, image_url: Optional[str] = None, audio_url: Optional[str] = None) -> Dict[str, Any]:
    start_time = time.time()
    scene_id = str(uuid.uuid4())
    story_id_str = str(story_id)
    
    scene_data = {
        "scene_id": scene_id,
        "story_id": story_id_str,
        "sequence": sequence,
        "text": text,
        "image_url": image_url,
        "audio_url": audio_url
    }
    
    logger.info(f"Creating new scene for story ID: {story_id_str}, sequence: {sequence}")
    self._log_operation("insert", "scenes", scene_data)
    
    try:
        response = self.client.table("scenes").insert(scene_data).execute()
        
        if not response.data:
            logger.error(f"Failed to create scene: No data returned from database")
            return None
            
        elapsed = time.time() - start_time
        logger.info(f"Scene created successfully in {elapsed:.2f}s: {scene_id}")
        return response.data[0]
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to create scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

#### Get Story Scenes

```python
async def get_story_scenes(self, story_id: str) -> List[Dict[str, Any]]:
    start_time = time.time()
    story_id_str = str(story_id)
    
    logger.info(f"Getting scenes for story ID: {story_id_str}")
    self._log_operation("select", "scenes", filters={"story_id": story_id_str})
    
    try:
        response = self.client.table("scenes").select("*").eq("story_id", story_id_str).order("sequence").execute()
        scenes = response.data if response.data else []
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(scenes)} scenes successfully in {elapsed:.2f}s for story: {story_id_str}")
        return scenes
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to get scenes in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Batch Operations

#### Batch Insert Scenes

```python
async def batch_insert_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    start_time = time.time()
    
    if not scenes:
        logger.warning("No scenes provided for batch insert")
        return []
        
    # Ensure all scenes have scene_id
    for scene in scenes:
        if "scene_id" not in scene:
            scene["scene_id"] = str(uuid.uuid4())
            
    logger.info(f"Batch inserting {len(scenes)} scenes")
    self._log_operation("insert", "scenes", {"count": len(scenes)})
    
    try:
        response = self.client.table("scenes").insert(scenes).execute()
        inserted = response.data if response.data else []
        
        elapsed = time.time() - start_time
        logger.info(f"Batch inserted {len(inserted)} scenes in {elapsed:.2f}s")
        return inserted
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to batch insert scenes in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

## Storage Operations

### Ensure Bucket Exists

```python
async def _ensure_bucket_exists(self, bucket_name: str, public: bool = True) -> None:
    logger.debug(f"Ensuring bucket exists: {bucket_name}")
    try:
        # Try to get the bucket
        self.client.storage.get_bucket(bucket_name)
        logger.debug(f"Bucket already exists: {bucket_name}")
    except Exception as e:
        # Bucket doesn't exist, create it
        logger.info(f"Creating bucket: {bucket_name}, public: {public}")
        try:
            self.client.storage.create_bucket(bucket_name, public=public)
            logger.info(f"Bucket created successfully: {bucket_name}")
        except Exception as create_error:
            logger.error(f"Failed to create bucket {bucket_name}: {str(create_error)}", exc_info=True)
            raise
```

### Upload Image

```python
async def upload_image(self, story_id: str, scene_sequence: int, image_bytes: bytes) -> str:
    start_time = time.time()
    story_id_str = str(story_id)
    bucket_name = "story-images"
    file_path = f"{story_id_str}/{scene_sequence}.png"
    
    logger.info(f"Uploading image for story: {story_id_str}, scene: {scene_sequence}")
    
    try:
        # Ensure the bucket exists
        await self._ensure_bucket_exists(bucket_name)
        
        # Check if image data is valid
        if not image_bytes or len(image_bytes) < 100:
            logger.error(f"Invalid image data: too small or empty ({len(image_bytes) if image_bytes else 0} bytes)")
            raise ValueError("Invalid image data: too small or empty")
            
        # Upload the image
        logger.debug(f"Uploading image to {bucket_name}/{file_path}")
        self.client.storage.from_(bucket_name).upload(
            file_path,
            io.BytesIO(image_bytes),
            file_options={"content-type": "image/png"}
        )
        
        # Get the public URL
        public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
        
        elapsed = time.time() - start_time
        logger.info(f"Image uploaded successfully in {elapsed:.2f}s: {public_url}")
        return public_url
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to upload image in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Upload Audio

```python
async def upload_audio(self, story_id: str, scene_sequence: int, audio_bytes: bytes) -> str:
    start_time = time.time()
    story_id_str = str(story_id)
    bucket_name = "story-audio"
    file_path = f"{story_id_str}/{scene_sequence}.mp3"
    
    logger.info(f"Uploading audio for story: {story_id_str}, scene: {scene_sequence}")
    
    try:
        # Ensure the bucket exists
        await self._ensure_bucket_exists(bucket_name)
        
        # Check if audio data is valid
        if not audio_bytes or len(audio_bytes) < 100:
            logger.error(f"Invalid audio data: too small or empty ({len(audio_bytes) if audio_bytes else 0} bytes)")
            raise ValueError("Invalid audio data: too small or empty")
            
        # Upload the audio
        logger.debug(f"Uploading audio to {bucket_name}/{file_path}")
        self.client.storage.from_(bucket_name).upload(
            file_path,
            io.BytesIO(audio_bytes),
            file_options={"content-type": "audio/mpeg"}
        )
        
        # Get the public URL
        public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
        
        elapsed = time.time() - start_time
        logger.info(f"Audio uploaded successfully in {elapsed:.2f}s: {public_url}")
        return public_url
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to upload audio in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Delete File

```python
async def delete_file(self, bucket_name: str, file_path: str) -> bool:
    start_time = time.time()
    
    logger.info(f"Deleting file from {bucket_name}: {file_path}")
    
    try:
        # Check if the bucket exists
        try:
            self.client.storage.get_bucket(bucket_name)
        except Exception:
            logger.warning(f"Bucket does not exist: {bucket_name}")
            return False
            
        # Delete the file
        self.client.storage.from_(bucket_name).remove([file_path])
        
        elapsed = time.time() - start_time
        logger.info(f"File deleted successfully in {elapsed:.2f}s: {bucket_name}/{file_path}")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to delete file in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return False
```

### List Bucket Files

```python
async def list_bucket_files(self, bucket_name: str, path: str = "") -> List[Dict[str, Any]]:
    start_time = time.time()
    
    logger.info(f"Listing files in bucket: {bucket_name}, path: {path}")
    
    try:
        # Check if the bucket exists
        try:
            self.client.storage.get_bucket(bucket_name)
        except Exception:
            logger.warning(f"Bucket does not exist: {bucket_name}")
            return []
            
        # List files
        response = self.client.storage.from_(bucket_name).list(path)
        files = response if response else []
        
        elapsed = time.time() - start_time
        logger.info(f"Listed {len(files)} files in {elapsed:.2f}s from bucket: {bucket_name}")
        return files
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to list files in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

## Advanced Query Examples

### Search Stories by Title or Prompt

```python
async def search_stories(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    start_time = time.time()
    
    logger.info(f"Searching stories for term: {search_term}, limit: {limit}")
    self._log_operation("select", "stories", filters={"search": search_term, "limit": limit})
    
    try:
        # Use ilike for case-insensitive search in both title and prompt
        response = self.client.table("stories").select("*").or_(f"title.ilike.%{search_term}%,prompt.ilike.%{search_term}%").limit(limit).execute()
        stories = response.data if response.data else []
        
        elapsed = time.time() - start_time
        logger.info(f"Found {len(stories)} stories in {elapsed:.2f}s for search term: {search_term}")
        return stories
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to search stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Get Recent Stories

```python
async def get_recent_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
    start_time = time.time()
    
    logger.info(f"Getting recent stories with limit: {limit}")
    self._log_operation("select", "stories", filters={"limit": limit, "order": "created_at.desc"})
    
    try:
        response = self.client.table("stories").select("*").order("created_at", desc=True).limit(limit).execute()
        stories = response.data if response.data else []
        
        elapsed = time.time() - start_time
        logger.info(f"Retrieved {len(stories)} recent stories in {elapsed:.2f}s")
        return stories
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to get recent stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

### Count Stories by Status

```python
async def count_stories(self, status: Optional[str] = None) -> int:
    start_time = time.time()
    
    logger.info(f"Counting stories with status filter: {status if status else 'None'}")
    self._log_operation("select", "stories", filters={"status": status, "count": "exact"})
    
    try:
        query = self.client.table("stories").select("*", count="exact")
        
        if status:
            query = query.eq("status", status)
            
        response = query.execute()
        count = response.count if hasattr(response, 'count') else 0
        
        elapsed = time.time() - start_time
        logger.info(f"Counted {count} stories in {elapsed:.2f}s")
        return count
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to count stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
        raise
```

## Utility Methods

### Operation Logging Helper

```python
def _log_operation(self, operation: str, table: str, data: Any = None, filters: Dict[str, Any] = None) -> None:
    log_data = {
        "operation": operation,
        "table": table
    }
    
    if data:
        # Limit data logging to avoid excessive log size
        if isinstance(data, dict):
            # Log only keys for dictionaries
            log_data["data_keys"] = list(data.keys())
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # For list of dicts, log count and keys of first item
            log_data["data_count"] = len(data)
            log_data["data_keys"] = list(data[0].keys()) if data else []
    
    if filters:
        log_data["filters"] = filters
        
    logger.debug(f"Database operation: {log_data}")
```

### Connection Health Check

```python
async def check_connection(self) -> bool:
    start_time = time.time()
    
    logger.info("Checking Supabase connection")
    
    try:
        # Try a simple query to check connection
        self.client.table("users").select("count(*)", count="exact").limit(1).execute()
        
        elapsed = time.time() - start_time
        logger.info(f"Supabase connection check successful in {elapsed:.2f}s")
        return True
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Supabase connection check failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
        return False
```

## Error Handling Patterns

### Retry Logic for Timeouts

```python
async def query_with_retry(self, table: str, query_fn) -> Any:
    max_retries = 3
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            start_time = time.time()
            result = query_fn(self.client.table(table))
            elapsed = time.time() - start_time
            logger.info(f"Query executed successfully in {elapsed:.2f}s")
            return result
        except Exception as e:
            retry_count += 1
            last_error = e
            wait_time = retry_count * 2  # Exponential backoff
            
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                logger.warning(f"Query attempt {retry_count} failed with connection issue: {str(e)}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                # Not a connection issue, don't retry
                logger.error(f"Query failed with non-connection error: {str(e)}", exc_info=True)
                raise
    
    logger.error(f"Query failed after {max_retries} retries: {str(last_error)}", exc_info=True)
    raise last_error
```

### Transaction Example

```python
async def create_story_with_scenes(self, story_data: Dict[str, Any], scenes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Note: Supabase JS has transaction support, but Python client doesn't have direct transaction support
    # This is a manual transaction pattern with rollback handling
    
    story = None
    scenes = []
    
    try:
        # Step 1: Create the story
        story = await self.create_story(
            title=story_data["title"],
            prompt=story_data["prompt"],
            user_id=story_data.get("user_id")
        )
        
        if not story:
            raise Exception("Failed to create story")
            
        story_id = story["story_id"]
        
        # Step 2: Create all scenes for this story
        for scene_data in scenes_data:
            scene_data["story_id"] = story_id
            scene = await self.create_scene(
                story_id=story_id,
                sequence=scene_data["sequence"],
                text=scene_data["text"],
                image_url=scene_data.get("image_url"),
                audio_url=scene_data.get("audio_url")
            )
            scenes.append(scene)
            
        # Step 3: Update story status to completed
        await self.update_story_status(story_id, "COMPLETED")
        
        return {
            "story": story,
            "scenes": scenes
        }
    except Exception as e:
        # Manual rollback
        if story:
            logger.warning(f"Error occurred during story creation, rolling back: {str(e)}")
            story_id = story["story_id"]
            
            # Delete any scenes that were created
            if scenes:
                try:
                    for scene in scenes:
                        await self.delete_scene(scene["scene_id"])
                except Exception as scene_del_error:
                    logger.error(f"Error during scene rollback: {str(scene_del_error)}", exc_info=True)
            
            # Delete the story
            try:
                await self.delete_story(story_id)
            except Exception as story_del_error:
                logger.error(f"Error during story rollback: {str(story_del_error)}", exc_info=True)
                
        # Re-raise the original exception
        logger.error(f"Failed to create story with scenes: {str(e)}", exc_info=True)
        raise
```

## API Endpoints

### User Endpoints

```python
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to create user with email: {user.email}")
    
    try:
        user_data = await service.create_user(user.email, user.username)
        logger.info(f"User created successfully: {user_data['user_id']}")
        return UserResponse(**user_data)
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to get user with ID: {user_id}")
    
    try:
        user_data = await service.get_user(user_id)
        
        if not user_data:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.info(f"User retrieved successfully: {user_id}")
        return UserResponse(**user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@router.get("/users/{user_id}/stories", response_model=UserStoriesResponse)
async def get_user_stories(user_id: str, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to get stories for user ID: {user_id}")
    
    try:
        user_data = await service.get_user(user_id)
        
        if not user_data:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
            
        stories = await service.get_user_stories(user_id)
        logger.info(f"Retrieved {len(stories)} stories for user: {user_id}")
        
        return UserStoriesResponse(
            user=UserResponse(**user_data),
            stories=[StoryResponse(**story) for story in stories]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user stories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user stories: {str(e)}")
```

### Story Endpoints

```python
@router.post("/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(story: StoryRequest, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to create story with title: {story.title}")
    
    try:
        story_data = await service.create_new_story(story.title, story.prompt, story.user_id)
        logger.info(f"Story created successfully: {story_data['story_id']}")
        return StoryResponse(**story_data)
    except Exception as e:
        logger.error(f"Failed to create story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create story: {str(e)}")

@router.get("/stories/{story_id}", response_model=StoryDetail)
async def get_story(story_id: str, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to get story with ID: {story_id}")
    
    try:
        story_detail = await service.get_story_detail(story_id)
        
        if not story_detail:
            logger.warning(f"Story not found with ID: {story_id}")
            raise HTTPException(status_code=404, detail="Story not found")
            
        logger.info(f"Story retrieved successfully: {story_id}")
        return story_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get story: {str(e)}")

@router.put("/stories/{story_id}/status", response_model=StoryResponse)
async def update_story_status(story_id: str, status: StoryStatus, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to update story status: {story_id} -> {status.value}")
    
    try:
        success = await service.update_story_status(story_id, status)
        
        if not success:
            logger.warning(f"Story not found with ID: {story_id}")
            raise HTTPException(status_code=404, detail="Story not found")
            
        story = await service.get_story_status(story_id)
        logger.info(f"Story status updated successfully: {story_id} -> {status.value}")
        return story
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update story status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update story status: {str(e)}")
```

## New API Endpoints

### Search Stories

```python
@router.get("/stories/search", response_model=List[StoryResponse])
async def search_stories(query: str, limit: int = 10, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to search stories with query: {query}, limit: {limit}")
    
    try:
        stories = await service.search_stories(query, limit)
        logger.info(f"Found {len(stories)} stories matching query: {query}")
        return [StoryResponse(**story) for story in stories]
    except Exception as e:
        logger.error(f"Failed to search stories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search stories: {str(e)}")
```

### Get Recent Stories

```python
@router.get("/stories/recent", response_model=List[StoryResponse])
async def get_recent_stories(limit: int = 10, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to get recent stories with limit: {limit}")
    
    try:
        stories = await service.get_recent_stories(limit)
        logger.info(f"Retrieved {len(stories)} recent stories")
        return [StoryResponse(**story) for story in stories]
    except Exception as e:
        logger.error(f"Failed to get recent stories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get recent stories: {str(e)}")
```

### Delete Story

```python
@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(story_id: str, service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to delete story with ID: {story_id}")
    
    try:
        success = await service.delete_story(story_id)
        
        if not success:
            logger.warning(f"Story not found with ID: {story_id}")
            raise HTTPException(status_code=404, detail="Story not found")
            
        logger.info(f"Story deleted successfully: {story_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")
```

### Update User

```python
@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: Dict[str, Any], service: StoryService = Depends(get_story_service)):
    logger.info(f"API request to update user with ID: {user_id}, fields: {list(user_data.keys())}")
    
    try:
        updated_user = await service.update_user(user_id, user_data)
        
        if not updated_user:
            logger.warning(f"User not found with ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.info(f"User updated successfully: {user_id}")
        return UserResponse(**updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
```

