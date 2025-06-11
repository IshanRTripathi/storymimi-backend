from typing import Dict, List, Optional, Any
from uuid import UUID
import logging

from app.database.supabase_client import SupabaseClient
from app.models.story import StoryRequest, StoryStatus, StoryDetail, Scene
from app.workers.celery_app import celery_app

# Create a logger for this module
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
        try:
            story = await self.db_client.get_story(story_id)
            if not story:
                raise Exception(f"Story with ID {story_id} not found")
            
            return {
                "story_id": story["story_id"],
                "status": story["status"]
            }
        except Exception as e:
            # Log the error and re-raise
            print(f"Error getting story status: {str(e)}")
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
        try:
            # Get the story record
            story = await self.db_client.get_story(story_id)
            if not story:
                raise Exception(f"Story with ID {story_id} not found")
            
            # Get all scenes for the story
            scenes_data = await self.db_client.get_story_scenes(story_id)
            
            # Convert scenes data to Scene objects
            scenes = [Scene(**scene_data) for scene_data in scenes_data]
            
            # Create and return a StoryDetail object
            return StoryDetail(
                story_id=story["story_id"],
                title=story["title"],
                status=story["status"],
                user_id=story.get("user_id"),
                created_at=story["created_at"],
                updated_at=story.get("updated_at"),
                scenes=scenes
            )
        except Exception as e:
            # Log the error and re-raise
            print(f"Error getting story detail: {str(e)}")
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
        try:
            # Query the database for all stories belonging to the user
            response = self.db_client.client.table("stories").select("*").eq("user_id", str(user_id)).execute()
            return response.data if response.data else []
        except Exception as e:
            # Log the error and re-raise
            print(f"Error getting user stories: {str(e)}")
            raise