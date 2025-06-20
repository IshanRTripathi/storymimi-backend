from typing import Dict, Optional, Any, Union, List
from uuid import UUID
from datetime import datetime

from app.database.supabase_client.base_client import SupabaseBaseClient
from app.models.story_types import StoryStatus

import logging
import time
import uuid

logger = logging.getLogger(__name__)

class StoryRepository(SupabaseBaseClient):
    """Repository for story-related operations"""
    
    async def create_story(self, title: str, prompt: str, user_id: Optional[Union[str, UUID]] = None, story_metadata: Optional[Dict[str, Any]] = None, source: Optional[str] = "user") -> Dict[str, Any]:
        """Create a new story record with PENDING status
        
        Args:
            title: The title of the story
            prompt: The prompt for story generation
            user_id: Optional ID of the user creating the story
            story_metadata: Optional structured JSON data generated by LLM
            source: Optional string indicating the source of the creation (e.g., "user", "llm")
            
        Returns:
            The created story data or None if creation failed
            
        Raises:
            Exception: If story creation fails
        """
        start_time = time.time()
        story_id = uuid.uuid4()
        story_id_str = str(story_id)
        user_id_str = str(user_id) if user_id else None
        
        # Create story data with timestamps
        now = datetime.now().isoformat()
        story_data = {
            "story_id": story_id_str,
            "title": title,
            "prompt": prompt,
            "status": StoryStatus.PENDING,
            "created_at": now,
            "updated_at": now,
            "story_metadata": story_metadata,
            "source": source
        }
        
        if user_id:
            story_data["user_id"] = user_id_str
            
        self._log_operation("insert", "stories", story_data)
        logger.info(f"Creating story with ID: {story_id_str}")
        
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
    
    async def update_story_status(self, story_id: Union[str, UUID], status: StoryStatus, user_id: Optional[str] = None, source: Optional[str] = None) -> bool:
        """Update the status of a story with audit trail
        
        Args:
            story_id: The ID of the story to update
            status: The new status to set
            user_id: Optional Firebase UID of user performing the update
            source: Optional string indicating the source of the update (e.g., "user", "system")
            
        Returns:
            True if update was successful, False otherwise
            
        Raises:
            Exception: If status update fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            "updated_by": user_id,
            "source": source
        }
        
        self._log_operation("update", "stories", update_data, filters={"story_id": story_id_str})
        logger.info(f"Updating story status to {status} for ID: {story_id_str}")
        
        try:
            response = self.client.table("stories").update(update_data).eq("story_id", story_id_str).execute()
            
            if not response.data:
                logger.warning(f"Story status update failed, no data returned: {story_id_str}")
                return False
            
            elapsed = time.time() - start_time
            logger.info(f"Story status updated successfully in {elapsed:.2f}s: {story_id_str}")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update story status in {elapsed:.2f}s: {str(e)}", exc_info=True)
            return False
    
    async def update_story(self, story_id: Union[str, UUID], data: Dict[str, Any], user_id: Optional[str] = None, source: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update a story's information with audit trail
        
        Args:
            story_id: The ID of the story to update
            data: Dictionary containing fields to update
            user_id: Optional Firebase UID of user performing the update
            source: Optional string indicating the source of the update (e.g., "user", "system")
            
        Returns:
            The updated story data or None if update failed
            
        Raises:
            Exception: If story update fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        # Convert datetime to ISO string
        update_data = {
            **data,
            "updated_at": datetime.now().isoformat(),
            "updated_by": user_id,
            "source": source
        }
        
        self._log_operation("update", "stories", update_data, filters={"story_id": story_id_str})
        logger.info(f"Updating story with ID: {story_id_str}, fields: {list(data.keys())}")
        
        try:
            response = self.client.table("stories").update(update_data).eq("story_id", story_id_str).execute()
            
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

    async def update_story_cover_image_if_null(self, story_id: Union[str, UUID], cover_image_url: str) -> bool:
        """Update a story's cover image only if it's currently null/empty
        
        Args:
            story_id: The ID of the story to update
            cover_image_url: The URL of the cover image
            
        Returns:
            True if cover image was updated, False if already set or update failed
            
        Raises:
            Exception: If cover image update fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        logger.info(f"Checking and updating cover image for story: {story_id_str}")
        
        try:
            # First, get the current story to check if cover image is already set
            story_data = await self.get_story(story_id_str)
            if not story_data:
                logger.warning(f"Story not found: {story_id_str}")
                return False
            
            # Check if cover image is already set
            current_cover_image = story_data.get("cover_image_url")
            if current_cover_image and current_cover_image.strip():
                logger.info(f"Story {story_id_str} already has cover image: {current_cover_image}")
                return False
            
            # Update cover image
            update_data = {
                "cover_image_url": cover_image_url,
                "updated_at": datetime.now().isoformat()
            }
            
            self._log_operation("update", "stories", update_data, filters={"story_id": story_id_str})
            logger.info(f"Setting cover image for story {story_id_str}: {cover_image_url}")
            
            response = self.client.table("stories").update(update_data).eq("story_id", story_id_str).execute()
            
            if not response.data:
                logger.warning(f"Cover image update failed, no data returned: {story_id_str}")
                return False
                
            elapsed = time.time() - start_time
            logger.info(f"Cover image updated successfully in {elapsed:.2f}s for story: {story_id_str}")
            return True
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update cover image in {elapsed:.2f}s: {str(e)}", exc_info=True)
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
    
    async def count_stories(self, status: Optional[StoryStatus] = None) -> int:
        """Count stories, optionally filtered by status
        
        Args:
            status: Optional status to filter by
            
        Returns:
            The total count of stories matching the criteria
            
        Raises:
            Exception: If query fails
        """
        start_time = time.time()
        
        filters = {}
        if status:
            filters["status"] = status
        
        self._log_operation("count", "stories", filters=filters)
        logger.info(f"Counting stories with filters: {filters}")
        
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
        finally:
            self._log_operation("count", "stories", result=count)
    
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

    async def get_story_scenes(self, story_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """Get all scenes for a story
        
        Args:
            story_id: The ID of the story to get scenes for
            
        Returns:
            List of scene dictionaries
            
        Raises:
            Exception: If scene retrieval fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        self._log_operation("select", "scenes", filters={"story_id": story_id_str})
        logger.info(f"Getting scenes for story with ID: {story_id_str}")
        
        try:
            response = self.client.table("scenes").select("*").eq("story_id", story_id_str).order("sequence").execute()
            scenes = response.data if response.data else []
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(scenes)} scenes in {elapsed:.2f}s for story: {story_id_str}")
            return scenes
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get scenes in {elapsed:.2f}s: {str(e)}", exc_info=True)
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

    async def get_stories_by_user_id(self, user_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """Get all stories created by a user
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of story dictionaries
            
        Raises:
            Exception: If retrieval fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("select", "stories", filters={"user_id": user_id_str})
        logger.info(f"Getting stories for user: {user_id_str}")
        
        try:
            # Add debug logging for Supabase client
            logger.debug(f"Supabase client initialized: {self.client is not None}")
            logger.debug(f"Querying stories table for user_id: {user_id_str}")
            
            response = self.client.table("stories").select("*").eq("user_id", user_id_str).order("created_at", desc=True).execute()
            
            # Add debug logging for response
            logger.debug(f"Supabase response received: {response is not None}")
            logger.debug(f"Response data type: {type(response.data) if hasattr(response, 'data') else 'No data attribute'}")
            
            stories = response.data if response.data else []
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(stories)} stories in {elapsed:.2f}s for user: {user_id_str}")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get user stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {e}")
            raise
