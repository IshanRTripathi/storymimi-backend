import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID

from app.database.supabase_client import SupabaseClient
from app.models.story import StoryStatus, StoryRequest, StoryResponse, StoryDetail, Scene
from app.models.user import UserResponse
from app.workers.story_worker import generate_story_task

logger = logging.getLogger(__name__)

class StoryService:
    """Service for orchestrating story creation and management"""
    
    def __init__(self):
        """Initialize the StoryService with a Supabase client"""
        self.db_client = SupabaseClient()
    
    async def create_new_story(self, request: StoryRequest) -> Dict[str, Any]:
        """Create a new story and dispatch the generation task to Celery
        
        Args:
            request: The StoryRequest containing story details
            
        Returns:
            A dictionary with story_id and status
            
        Raises:
            Exception: If story creation fails
        """
        logger.info(f"Creating new story with title: {request.title}, prompt: {request.prompt[:50]}..., user_id: {request.user_id}")
        try:
            # Create a new story record in Supabase with PENDING status
            logger.debug("Creating story record in database")
            story = await self.db_client.create_story(
                title=request.title,
                prompt=request.prompt,
                user_id=request.user_id
            )
            
            if not story:
                logger.error("Failed to create story record in database")
                raise Exception("Failed to create story record")
            
            # Get the story_id
            story_id = story["story_id"]
            logger.info(f"Story record created with ID: {story_id}")
            
            # Dispatch the generate_story_task to Celery
            logger.debug(f"Dispatching generate_story_task to Celery for story ID: {story_id}")
            from app.workers.story_worker import generate_story_task
            generate_story_task.delay(story_id=story_id, request_dict=request.dict())
            logger.info(f"Story generation task dispatched for story ID: {story_id}")
            
            # Return a dictionary with story_id and status
            return {
                "story_id": story_id,
                "status": StoryStatus.PENDING.value
            }
        except Exception as e:
            # Log the error and re-raise
            logger.exception(f"Error creating story: {str(e)}")
            raise
    
    async def get_story_status(self, story_id: UUID) -> Dict[str, Any]:
        """Get the current status of a story
        
        Args:
            story_id: The ID of the story
            
        Returns:
            A dictionary with story_id and status
            
        Raises:
            Exception: If story retrieval fails
        """
        logger.info(f"Getting status for story ID: {story_id}")
        start_time = time.time()
        
        try:
            story = await self.db_client.get_story(story_id)
            if not story:
                logger.warning(f"Story with ID {story_id} not found")
                raise Exception(f"Story with ID {story_id} not found")
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved status for story ID: {story_id} in {elapsed:.2f}s: {story['status']}")
            
            return {
                "story_id": story["story_id"],
                "status": story["status"]
            }
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting story status in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_story_detail(self, story_id: UUID) -> StoryDetail:
        """Get the full details of a story including all scenes
        
        Args:
            story_id: The ID of the story
            
        Returns:
            A StoryDetail object with all story information
            
        Raises:
            Exception: If story retrieval fails
        """
        logger.info(f"Getting full details for story ID: {story_id}")
        start_time = time.time()
        
        try:
            # Get the story record
            story = await self.db_client.get_story(story_id)
            if not story:
                logger.warning(f"Story with ID {story_id} not found")
                raise Exception(f"Story with ID {story_id} not found")
            
            # Get all scenes for the story
            logger.debug(f"Retrieving scenes for story ID: {story_id}")
            scenes_data = await self.db_client.get_story_scenes(story_id)
            
            # Convert scenes data to Scene objects
            scenes = [Scene(**scene_data) for scene_data in scenes_data]
            logger.debug(f"Retrieved {len(scenes)} scenes for story ID: {story_id}")
            
            # Create and return a StoryDetail object
            story_detail = StoryDetail(
                story_id=story["story_id"],
                title=story["title"],
                status=story["status"],
                user_id=story.get("user_id"),
                created_at=story["created_at"],
                updated_at=story.get("updated_at"),
                scenes=scenes
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved full details for story ID: {story_id} in {elapsed:.2f}s, title: {story['title']}, scenes: {len(scenes)}")
            
            return story_detail
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting story detail in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_user_stories(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all stories for a user
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A list of story dictionaries
            
        Raises:
            Exception: If story retrieval fails
        """
        logger.info(f"Getting stories for user ID: {user_id}")
        start_time = time.time()
        
        try:
            # Get user stories from the database
            stories = await self.db_client.get_user_stories(user_id)
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(stories)} stories for user ID: {user_id} in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting user stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
            
    async def search_stories(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for stories by title or prompt
        
        Args:
            search_term: The search term to look for in titles and prompts
            limit: Maximum number of results to return
            
        Returns:
            A list of story dictionaries matching the search term
            
        Raises:
            Exception: If search fails
        """
        logger.info(f"Searching stories with term: {search_term}, limit: {limit}")
        start_time = time.time()
        
        try:
            # Search for stories in the database
            stories = await self.db_client.search_stories(search_term, limit)
            
            elapsed = time.time() - start_time
            logger.info(f"Found {len(stories)} stories matching search term: {search_term} in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error searching stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_recent_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recently created stories
        
        Args:
            limit: Maximum number of stories to return
            
        Returns:
            A list of recent story dictionaries
            
        Raises:
            Exception: If retrieval fails
        """
        logger.info(f"Getting recent stories with limit: {limit}")
        start_time = time.time()
        
        try:
            # Get recent stories from the database
            stories = await self.db_client.get_recent_stories(limit)
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(stories)} recent stories in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting recent stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def delete_story(self, story_id: UUID) -> bool:
        """Delete a story and all its associated scenes and files
        
        Args:
            story_id: The ID of the story to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If deletion fails
        """
        logger.info(f"Deleting story with ID: {story_id}")
        start_time = time.time()
        
        try:
            # First, check if the story exists
            story = await self.db_client.get_story(story_id)
            if not story:
                logger.warning(f"Story with ID {story_id} not found for deletion")
                return False
                
            # Delete all associated files (images and audio)
            try:
                await self.db_client.delete_story_files(story_id)
            except Exception as file_error:
                logger.warning(f"Error deleting story files: {str(file_error)}", exc_info=True)
                # Continue with deletion even if file deletion fails
            
            # Delete the story from the database
            success = await self.db_client.delete_story(story_id)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"Story deleted successfully in {elapsed:.2f}s: {story_id}")
            else:
                logger.warning(f"Story deletion returned no data in {elapsed:.2f}s: {story_id}")
                
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error deleting story in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def update_user(self, user_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user's information
        
        Args:
            user_id: The ID of the user to update
            data: Dictionary of fields to update
            
        Returns:
            The updated user data
            
        Raises:
            Exception: If update fails
        """
        logger.info(f"Updating user with ID: {user_id}, fields: {list(data.keys())}")
        start_time = time.time()
        
        try:
            # First, check if the user exists
            user = await self.db_client.get_user(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for update")
                return None
                
            # Update the user in the database
            updated_user = await self.db_client.update_user(user_id, data)
            
            elapsed = time.time() - start_time
            if updated_user:
                logger.info(f"User updated successfully in {elapsed:.2f}s: {user_id}")
            else:
                logger.warning(f"User update returned no data in {elapsed:.2f}s: {user_id}")
                
            return updated_user
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error updating user in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def update_story_status(self, story_id: UUID, status: StoryStatus) -> bool:
        """Update the status of a story
        
        Args:
            story_id: The ID of the story
            status: The new status to set
            
        Returns:
            True if update was successful, False otherwise
            
        Raises:
            Exception: If update fails
        """
        logger.info(f"Updating status for story ID: {story_id} to {status.value}")
        start_time = time.time()
        
        try:
            # Update the story status in the database
            success = await self.db_client.update_story_status(story_id, status.value)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"Story status updated successfully in {elapsed:.2f}s: {story_id} -> {status.value}")
            else:
                logger.warning(f"Story status update returned no data in {elapsed:.2f}s: {story_id}")
                
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error updating story status in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise