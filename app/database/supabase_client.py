import io
import uuid
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import UUID

from supabase.client import create_client, Client

from app.config import settings
from app.models.story import StoryStatus, Scene, StoryDetail
from app.models.user import User, UserResponse

# Create a logger for this module
logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client for interacting with Supabase database and storage"""
    
    def __init__(self):
        """Initialize the Supabase client with proper configuration"""
        logger.info("Initializing Supabase client")
        try:

            
            # Create the client with just the required parameters
            self.client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_KEY,
            )
            self.storage = self.client.storage
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}", exc_info=True)
            raise
            
    def _log_operation(self, operation: str, table: str, data: Any = None, filters: Any = None) -> None:
        """Log database operation details
        
        Args:
            operation: The operation being performed (select, insert, update, delete)
            table: The table being operated on
            data: The data being used in the operation (optional)
            filters: Any filters being applied (optional)
        """
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
    
    # User methods
    async def create_user(self, email: str, username: str) -> Dict[str, Any]:
        """Create a new user in the database
        
        Args:
            email: The user's email address
            username: The user's username
            
        Returns:
            The created user data or None if creation failed
            
        Raises:
            Exception: If user creation fails
        """
        start_time = time.time()
        user_id = str(uuid.uuid4())
        user_data = {
            "email": email,
            "username": username,
            "user_id": user_id
        }
        
        self._log_operation("insert", "users", user_data)
        logger.info(f"Creating new user with email: {email}, username: {username}, user_id: {user_id}")
        
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
    
    async def get_user(self, user_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a user by ID
        
        Args:
            user_id: The ID of the user to retrieve
            
        Returns:
            The user data or None if not found
            
        Raises:
            Exception: If user retrieval fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("select", "users", filters={"user_id": user_id_str})
        logger.info(f"Getting user with ID: {user_id_str}")
        
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
            
    async def update_user(self, user_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's information
        
        Args:
            user_id: The ID of the user to update
            data: Dictionary containing fields to update
            
        Returns:
            The updated user data or None if update failed
            
        Raises:
            Exception: If user update fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("update", "users", data, filters={"user_id": user_id_str})
        logger.info(f"Updating user with ID: {user_id_str}, fields: {list(data.keys())}")
        
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
            
    async def delete_user(self, user_id: Union[str, UUID]) -> bool:
        """Delete a user from the database
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If user deletion fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("delete", "users", filters={"user_id": user_id_str})
        logger.info(f"Deleting user with ID: {user_id_str}")
        
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
            
    async def get_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get a list of users with pagination
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user data dictionaries
            
        Raises:
            Exception: If user retrieval fails
        """
        start_time = time.time()
        
        self._log_operation("select", "users", filters={"limit": limit, "offset": offset})
        logger.info(f"Getting users with limit: {limit}, offset: {offset}")
        
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
    
    # Story methods
    async def create_story(self, title: str, prompt: str, user_id: Optional[Union[str, UUID]] = None) -> Dict[str, Any]:
        """Create a new story record with PENDING status
        
        Args:
            title: The title of the story
            prompt: The prompt for story generation
            user_id: Optional ID of the user creating the story
            
        Returns:
            The created story data or None if creation failed
            
        Raises:
            Exception: If story creation fails
        """
        start_time = time.time()
        story_id = uuid.uuid4()
        story_id_str = str(story_id)
        user_id_str = str(user_id) if user_id else None
        
        story_data = {
            "story_id": story_id_str,
            "title": title,
            "prompt": prompt,
            "status": StoryStatus.PENDING.value,
            "user_id": user_id_str
        }
        
        self._log_operation("insert", "stories", story_data)
        logger.info(f"Creating new story with ID: {story_id_str}, title: {title}, user_id: {user_id_str}")
        
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
    
    async def get_story(self, story_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a story by ID
        
        Args:
            story_id: The ID of the story to retrieve
            
        Returns:
            The story data or None if not found
            
        Raises:
            Exception: If story retrieval fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        self._log_operation("select", "stories", filters={"story_id": story_id_str})
        logger.info(f"Getting story with ID: {story_id_str}")
        
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
    
    async def update_story_status(self, story_id: Union[str, UUID], status: StoryStatus) -> bool:
        """Update the status of a story
        
        Args:
            story_id: The ID of the story to update
            status: The new status to set
            
        Returns:
            True if update was successful, False otherwise
            
        Raises:
            Exception: If status update fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        status_value = status.value
        
        self._log_operation("update", "stories", {"status": status_value}, filters={"story_id": story_id_str})
        logger.info(f"Updating story status for ID: {story_id_str} to {status_value}")
        
        try:
            # Update the story status
            response = self.client.table("stories") \
                .update({"status": status_value}) \
                .eq("story_id", story_id_str) \
                .execute()
            
            elapsed = time.time() - start_time
            
            # Validate response data
            if not response.data:
                logger.warning(f"No data returned from Supabase after updating story_id={story_id_str}. This is not an error.")
                return True
            
            logger.debug(f"Updated story: {response.data}")
            logger.info(f"Story status updated successfully in {elapsed:.2f}s: {story_id_str} -> {status_value}")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update story status in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    async def update_story(self, story_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a story's information
        
        Args:
            story_id: The ID of the story to update
            data: Dictionary containing fields to update
            
        Returns:
            The updated story data or None if update failed
            
        Raises:
            Exception: If story update fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        self._log_operation("update", "stories", data, filters={"story_id": story_id_str})
        logger.info(f"Updating story with ID: {story_id_str}, fields: {list(data.keys())}")
        
        try:
            response = self.client.table("stories").update(data).eq("story_id", story_id_str).execute()
            
            if not response.data:
                logger.warning(f"Story update failed, no data returned: {story_id_str}")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Story updated successfully in {elapsed:.2f}s: {story_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update story in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def delete_story(self, story_id: Union[str, UUID]) -> bool:
        """Delete a story and all its related scenes
        
        Args:
            story_id: The ID of the story to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If story deletion fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        self._log_operation("delete", "stories", filters={"story_id": story_id_str})
        logger.info(f"Deleting story with ID: {story_id_str}")
        
        try:
            # First delete all scenes associated with this story
            scenes_response = self.client.table("scenes").delete().eq("story_id", story_id_str).execute()
            scenes_deleted = len(scenes_response.data) if scenes_response.data else 0
            logger.info(f"Deleted {scenes_deleted} scenes for story: {story_id_str}")
            
            # Then delete the story itself
            response = self.client.table("stories").delete().eq("story_id", story_id_str).execute()
            success = bool(response.data)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"Story deleted successfully in {elapsed:.2f}s: {story_id_str}")
            else:
                logger.warning(f"Story deletion returned no data in {elapsed:.2f}s: {story_id_str}")
                
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete story in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def create_scene(self, story_id: Union[str, UUID], sequence: int, text: str, 
                          image_url: Optional[str] = None, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new scene for a story
        
        Args:
            story_id: The ID of the story this scene belongs to
            sequence: The sequence number of the scene
            text: The text content of the scene
            image_url: Optional URL to the scene's image
            audio_url: Optional URL to the scene's audio narration
            
        Returns:
            The created scene data or None if creation failed
            
        Raises:
            Exception: If scene creation fails
        """
        start_time = time.time()
        scene_id = uuid.uuid4()
        scene_id_str = str(scene_id)
        story_id_str = str(story_id)
        
        scene_data = {
            "scene_id": scene_id_str,
            "story_id": story_id_str,
            "sequence": sequence,
            "text": text,
            "image_url": image_url,
            "audio_url": audio_url
        }
        
        self._log_operation("insert", "scenes", scene_data)
        logger.info(f"Creating new scene with ID: {scene_id_str}, story_id: {story_id_str}, sequence: {sequence}")
        
        try:
            response = self.client.table("scenes").insert(scene_data).execute()
            
            if not response.data:
                logger.error(f"Failed to create scene: No data returned from database")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Scene created successfully in {elapsed:.2f}s: {scene_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to create scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def update_scene(self, scene_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a scene's information
        
        Args:
            scene_id: The ID of the scene to update
            data: Dictionary containing fields to update
            
        Returns:
            The updated scene data or None if update failed
            
        Raises:
            Exception: If scene update fails
        """
        start_time = time.time()
        scene_id_str = str(scene_id)
        
        self._log_operation("update", "scenes", data, filters={"scene_id": scene_id_str})
        logger.info(f"Updating scene with ID: {scene_id_str}, fields: {list(data.keys())}")
        
        try:
            response = self.client.table("scenes").update(data).eq("scene_id", scene_id_str).execute()
            
            if not response.data:
                logger.warning(f"Scene update failed, no data returned: {scene_id_str}")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Scene updated successfully in {elapsed:.2f}s: {scene_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_scene(self, scene_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a scene by ID
        
        Args:
            scene_id: The ID of the scene to retrieve
            
        Returns:
            The scene data or None if not found
            
        Raises:
            Exception: If scene retrieval fails
        """
        start_time = time.time()
        scene_id_str = str(scene_id)
        
        self._log_operation("select", "scenes", filters={"scene_id": scene_id_str})
        logger.info(f"Getting scene with ID: {scene_id_str}")
        
        try:
            response = self.client.table("scenes").select("*").eq("scene_id", scene_id_str).execute()
            
            if not response.data:
                logger.warning(f"Scene not found with ID: {scene_id_str}")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Scene retrieved successfully in {elapsed:.2f}s: {scene_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_story_scenes(self, story_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """Get all scenes for a story, ordered by sequence
        
        Args:
            story_id: The ID of the story to get scenes for
            
        Returns:
            List of scene data dictionaries
            
        Raises:
            Exception: If scene retrieval fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        self._log_operation("select", "scenes", filters={"story_id": story_id_str})
        logger.info(f"Getting scenes for story ID: {story_id_str}")
        
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
            
    async def delete_scene(self, scene_id: Union[str, UUID]) -> bool:
        """Delete a scene
        
        Args:
            scene_id: The ID of the scene to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If scene deletion fails
        """
        start_time = time.time()
        scene_id_str = str(scene_id)
        
        self._log_operation("delete", "scenes", filters={"scene_id": scene_id_str})
        logger.info(f"Deleting scene with ID: {scene_id_str}")
        
        try:
            response = self.client.table("scenes").delete().eq("scene_id", scene_id_str).execute()
            success = bool(response.data)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"Scene deleted successfully in {elapsed:.2f}s: {scene_id_str}")
            else:
                logger.warning(f"Scene deletion returned no data in {elapsed:.2f}s: {scene_id_str}")
                
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    # Storage methods
    async def _ensure_bucket_exists(self, bucket_name: str, public: bool = True) -> None:
        """Ensure a storage bucket exists, creating it if necessary
        
        Args:
            bucket_name: The name of the bucket
            public: Whether the bucket should be public
            
        Raises:
            Exception: If bucket creation fails
        """
        logger.debug(f"Ensuring bucket exists: {bucket_name}")
        try:
            # Try to get the bucket
            self.storage.get_bucket(bucket_name)
            logger.debug(f"Bucket already exists: {bucket_name}")
        except Exception as e:
            # Bucket doesn't exist, create it
            logger.info(f"Creating bucket: {bucket_name}, public: {public}")
            try:
                self.storage.create_bucket(bucket_name, public=public)
                logger.info(f"Bucket created successfully: {bucket_name}")
            except Exception as create_error:
                logger.error(f"Failed to create bucket {bucket_name}: {str(create_error)}", exc_info=True)
                raise
    
    async def upload_image(self, story_id: Union[str, UUID], scene_sequence: int, image_bytes: bytes) -> str:
        """Upload an image to Supabase Storage and return the public URL
        
        Args:
            story_id: The ID of the story
            scene_sequence: The sequence number of the scene
            image_bytes: The image data as bytes
            
        Returns:
            The public URL of the uploaded image
            
        Raises:
            Exception: If image upload fails
        """
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
            self.storage.from_(bucket_name).upload(
                file_path,
                io.BytesIO(image_bytes),
                file_options={"content-type": "image/png"}
            )
            
            # Get the public URL
            public_url = self.storage.from_(bucket_name).get_public_url(file_path)
            
            elapsed = time.time() - start_time
            logger.info(f"Image uploaded successfully in {elapsed:.2f}s: {public_url}")
            return public_url
        finally:
            # Log the end of the operation
            self._log_operation("upload", "images", success=True)
        
    # Advanced query methods
    async def count_stories(self, status: Optional[StoryStatus] = None) -> int:
        """Count stories, optionally filtered by status
        
        Args:
            status: Optional status to filter by
            
        Returns:
            The count of stories
            
        Raises:
            Exception: If counting fails
        """
        start_time = time.time()
        
        filters = {}
        if status:
            filters["status"] = status.value
            
        self._log_operation("count", "stories", filters=filters)
        logger.info(f"Counting stories with filters: {filters}")
        
        try:
            query = self.client.table("stories").select("*", count="exact")
            
            if status:
                query = query.eq("status", status.value)
                
            response = query.execute()
            count = response.count if hasattr(response, 'count') else 0
            
            elapsed = time.time() - start_time
            logger.info(f"Counted {count} stories in {elapsed:.2f}s")
            return count
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to count stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    async def search_stories(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for stories by title or prompt
        
        Args:
            search_term: The term to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching story dictionaries
            
        Raises:
            Exception: If search fails
        """
        start_time = time.time()
        
        self._log_operation("search", "stories", filters={"search_term": search_term, "limit": limit})
        logger.info(f"Searching stories for term: {search_term}, limit: {limit}")
        
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
            
    async def get_recent_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recently created stories
        
        Args:
            limit: Maximum number of stories to return
            
        Returns:
            List of story dictionaries
            
        Raises:
            Exception: If retrieval fails
        """
        start_time = time.time()
        
        self._log_operation("select", "stories", filters={"limit": limit, "order": "created_at.desc"})
        logger.info(f"Getting {limit} most recent stories")
        
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
            
    async def get_user_story_count(self, user_id: Union[str, UUID]) -> int:
        """Get the count of stories created by a user
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The count of stories
            
        Raises:
            Exception: If counting fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("count", "stories", filters={"user_id": user_id_str})
        logger.info(f"Counting stories for user: {user_id_str}")
        
        try:
            response = self.client.table("stories").select("*", count="exact").eq("user_id", user_id_str).execute()
            count = response.count if hasattr(response, 'count') else 0
            
            elapsed = time.time() - start_time
            logger.info(f"Counted {count} stories in {elapsed:.2f}s for user: {user_id_str}")
            return count
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to count user stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    # Batch operations
    async def batch_insert_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple scenes in a single operation
        
        Args:
            scenes: List of scene data dictionaries
            
        Returns:
            List of created scene data
            
        Raises:
            Exception: If batch insert fails
        """
        start_time = time.time()
        
        if not scenes:
            logger.warning("No scenes provided for batch insert")
            return []
            
        # Ensure all scenes have scene_id
        for scene in scenes:
            if "scene_id" not in scene:
                scene["scene_id"] = str(uuid.uuid4())
                
        self._log_operation("insert", "scenes", scenes)
        logger.info(f"Batch inserting {len(scenes)} scenes")
        
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
            
    async def upsert_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update a user
        
        Args:
            user_data: User data dictionary with user_id
            
        Returns:
            The upserted user data
            
        Raises:
            Exception: If upsert fails
        """
        start_time = time.time()
        
        if "user_id" not in user_data:
            user_data["user_id"] = str(uuid.uuid4())
            
        user_id = user_data["user_id"]
        
        self._log_operation("upsert", "users", user_data)
        logger.info(f"Upserting user with ID: {user_id}")
        
        try:
            response = self.client.table("users").upsert(user_data).execute()
            
            if not response.data:
                logger.error(f"Failed to upsert user: No data returned from database")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"User upserted successfully in {elapsed:.2f}s: {user_id}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to upsert user in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    # Health check and diagnostics
    async def check_connection(self) -> bool:
        """Check if the connection to Supabase is working
        
        Returns:
            True if connection is working, False otherwise
        """
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
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to upload image in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def upload_audio(self, story_id: Union[str, UUID], scene_sequence: int, audio_bytes: bytes) -> str:
        """Upload an audio file to Supabase Storage and return the public URL
        
        Args:
            story_id: The ID of the story
            scene_sequence: The sequence number of the scene
            audio_bytes: The audio data as bytes
            
        Returns:
            The public URL of the uploaded audio
            
        Raises:
            Exception: If audio upload fails
        """
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
            self.storage.from_(bucket_name).upload(
                file_path,
                io.BytesIO(audio_bytes),
                file_options={"content-type": "audio/mpeg"}
            )
            
            # Get the public URL
            public_url = self.storage.from_(bucket_name).get_public_url(file_path)
            
            elapsed = time.time() - start_time
            logger.info(f"Audio uploaded successfully in {elapsed:.2f}s: {public_url}")
            return public_url
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to upload audio in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Delete a file from Supabase Storage
        
        Args:
            bucket_name: The name of the bucket
            file_path: The path to the file within the bucket
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If file deletion fails
        """
        start_time = time.time()
        
        logger.info(f"Deleting file from {bucket_name}: {file_path}")
        
        try:
            # Check if the bucket exists
            try:
                self.storage.get_bucket(bucket_name)
            except Exception:
                logger.warning(f"Bucket does not exist: {bucket_name}")
                return False
                
            # Delete the file
            self.storage.from_(bucket_name).remove([file_path])
            
            elapsed = time.time() - start_time
            logger.info(f"File deleted successfully in {elapsed:.2f}s: {bucket_name}/{file_path}")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete file in {elapsed:.2f}s: {str(e)}", exc_info=True)
            return False
            
    async def delete_story_files(self, story_id: Union[str, UUID]) -> Tuple[int, int]:
        """Delete all files associated with a story
        
        Args:
            story_id: The ID of the story
            
        Returns:
            Tuple of (images_deleted, audio_files_deleted)
            
        Raises:
            Exception: If file deletion fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        logger.info(f"Deleting all files for story: {story_id_str}")
        
        try:
            # Get list of scenes to know what files to delete
            scenes = await self.get_story_scenes(story_id_str)
            
            images_deleted = 0
            audio_deleted = 0
            
            # Delete image files
            for scene in scenes:
                sequence = scene["sequence"]
                
                # Delete image
                image_path = f"{story_id_str}/{sequence}.png"
                if await self.delete_file("story-images", image_path):
                    images_deleted += 1
                    
                # Delete audio
                audio_path = f"{story_id_str}/{sequence}.mp3"
                if await self.delete_file("story-audio", audio_path):
                    audio_deleted += 1
            
            elapsed = time.time() - start_time
            logger.info(f"Deleted {images_deleted} images and {audio_deleted} audio files in {elapsed:.2f}s for story: {story_id_str}")
            return (images_deleted, audio_deleted)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete story files in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    async def list_bucket_files(self, bucket_name: str, path: str = "") -> List[Dict[str, Any]]:
        """List files in a bucket, optionally filtered by path prefix
        
        Args:
            bucket_name: The name of the bucket
            path: Optional path prefix to filter by
            
        Returns:
            List of file information dictionaries
            
        Raises:
            Exception: If listing files fails
        """
        start_time = time.time()
        
        logger.info(f"Listing files in bucket: {bucket_name}, path: {path}")
        
        try:
            # Check if the bucket exists
            try:
                self.storage.get_bucket(bucket_name)
            except Exception:
                logger.warning(f"Bucket does not exist: {bucket_name}")
                return []
                
            # List files
            response = self.storage.from_(bucket_name).list(path)
            files = response if response else []
            
            elapsed = time.time() - start_time
            logger.info(f"Listed {len(files)} files in {elapsed:.2f}s from bucket: {bucket_name}")
            return files
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to list files in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise