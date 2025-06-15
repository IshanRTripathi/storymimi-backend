from typing import Dict, Optional, Any, Union, List
from uuid import UUID
from datetime import datetime

from app.database.supabase_client.base_db_client import SupabaseBaseClient
from app.models.story_types import StoryStatus

import logging
import time
import uuid

logger = logging.getLogger(__name__)

class StoryRepository(SupabaseBaseClient):
    """Repository for story-related operations"""
    
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
        
        # Create story data with timestamps
        now = datetime.now().isoformat()
        story_data = {
            "story_id": story_id_str,
            "title": title,
            "prompt": prompt,
            "status": StoryStatus.PENDING,
            "created_at": now,
            "updated_at": now
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
    
    async def update_story_status(self, story_id: Union[str, UUID], status: StoryStatus, user_id: Optional[UUID] = None) -> bool:
        """Update the status of a story with audit trail
        
        Args:
            story_id: The ID of the story to update
            status: The new status to set
            user_id: Optional ID of user performing the update
            
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
            "updated_by": str(user_id) if user_id else None
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
    
    async def update_story(self, story_id: Union[str, UUID], data: Dict[str, Any], user_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Update a story's information with audit trail
        
        Args:
            story_id: The ID of the story to update
            data: Dictionary containing fields to update
            user_id: Optional ID of user performing the update
            
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
            "updated_by": str(user_id) if user_id else None
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
    
    async def create_scene(
        self,
        story_id: str,
        sequence: int,
        title: str,
        text: str,
        image_prompt: str,
        image_url: str,
        audio_url: str,
    ) -> Optional[Dict[str, Any]]:
        """Create a new scene for a story
        
        Args:
            story_id: ID of the story
            sequence: Sequence number of the scene
            title: Scene title
            text: Scene text content
            image_prompt: Prompt for generating the scene's image
            image_url: URL of the scene's image
            audio_url: URL of the scene's audio
            created_at: Creation timestamp (can be datetime or ISO string)
            updated_at: Last update timestamp (can be datetime or ISO string)
            
        Returns:
            The created scene data or None if creation failed
            
        Raises:
            Exception: If scene creation fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        # Generate scene_id
        scene_id = str(uuid.uuid4())
       
        # Generate timestamps
        now = datetime.now().isoformat()

        scene_data = {
            "scene_id": scene_id,
            "story_id": story_id_str,
            "sequence": sequence,
            "title": title,
            "text": text,
            "image_prompt": image_prompt,
            "image_url": image_url,
            "audio_url": audio_url,
            "created_at": now,
            "updated_at": now
        }
        
        self._log_operation("insert", "scenes", scene_data)
        logger.info(f"Creating scene {sequence} for story: {story_id_str}")
        
        try:
            response = self.client.table("scenes").insert(scene_data).execute()
            
            if not response.data:
                logger.error(f"Failed to create scene: No data returned from database")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Scene created successfully in {elapsed:.2f}s: {story_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to create scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
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
