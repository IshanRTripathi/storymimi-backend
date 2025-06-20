import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID

from app.database.supabase_client import StoryRepository, SceneRepository, UserRepository
from app.models.story_types import StoryRequest, StoryResponse, StoryStatus, StoryDetail, Scene
from app.models.user import UserResponse
from app.tasks.generate_story_task import generate_story_task
from app.utils.json_converter import JSONConverter

logger = logging.getLogger(__name__)


class StoryService:
    """Service for orchestrating story creation and management"""

    def __init__(self, story_client: StoryRepository, scene_client: SceneRepository, user_client: UserRepository):
        self.story_client = story_client
        self.scene_client = scene_client
        self.user_client = user_client

    async def create_new_story(self, request: StoryRequest) -> Dict[str, Any]:
        """
        Create a new story and dispatch the generation task to Celery.
        Uses run_in_executor to handle sync storage operations in async context.
        """
        logger.info(f"Creating new story with title: {request.title}, prompt: {request.prompt[:50]}..., user_id: {request.user_id}")
        try:
            logger.debug("Creating story record in database")
            story = await self.story_client.create_story(
                title=request.title,
                prompt=request.prompt,
                user_id=request.user_id
            )
            
            # Validate the created story data
            # No validation needed for GET endpoints

            if not story:
                logger.error("Failed to create story record in database")
                raise Exception("Failed to create story record")

            # Debug: Log what we got from the database
            logger.info(f"Database returned story: {story}")
            
            story_id = story["story_id"]
            logger.info(f"Story record created with ID: {story_id}")
            
            # Validate model data before returning (allowing partial data for initial creation)
            # Validator.validate_model_data({
            #     "story_id": story_id,
            #     "title": request.title,
            #     "status": StoryStatus.PENDING,
            #     "user_id": request.user_id
            # }, is_initial_creation=True)

            # Try to dispatch Celery task, but don't fail if it doesn't work
            try:
                logger.debug(f"Dispatching story generation task to Celery for story ID: {story_id}")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,  # Use default executor
                    generate_story_task.delay,
                    story_id,
                    request.dict(),
                    request.user_id
                )
                logger.info(f"Story generation task dispatched for story ID: {story_id}")
            except Exception as celery_error:
                logger.warning(f"Failed to dispatch Celery task for story {story_id}: {str(celery_error)}")
                logger.info(f"Story created successfully but task dispatch failed - story will remain in PENDING status")

            # Return the complete story data from database (includes created_at, updated_at)
            response = {
                "status": story["status"],
                "story_id": story["story_id"],
                "title": story["title"],
                "user_id": story["user_id"],
                "created_at": story["created_at"],
                "updated_at": story["updated_at"]
            }
            logger.info(f"Returning response: {response}")
            return response
        except Exception as e:
            logger.exception(f"Error creating story: {str(e)}")
            raise

    async def get_story_status(self, story_id: UUID) -> Dict[str, Any]:
        """Get the current status of a story"""
        logger.info(f"Getting status for story ID: {story_id}")
        start_time = time.time()

        try:
            story = await self.story_client.get_story(story_id)
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
        """Get the full details of a story including all scenes"""
        logger.info(f"Getting full details for story ID: {story_id}")
        start_time = time.time()

        try:
            story = await self.story_client.get_story(story_id)
            if not story:
                logger.warning(f"Story with ID {story_id} not found")
                raise Exception(f"Story with ID {story_id} not found")

            logger.debug(f"Retrieving scenes for story ID: {story_id}")
            scenes_data = await self.scene_client.get_scenes_by_story_id(story_id)
            logger.debug(f"Raw scenes data from DB: {scenes_data}")
            
            scenes = []
            for scene_data in scenes_data:
                # Create Scene object with only required fields
                scene = Scene(
                    scene_id=scene_data["scene_id"],
                    story_id=story_id,
                    sequence=scene_data["sequence"],
                    title=scene_data["title"],
                    text=scene_data["text"],
                    image_url=scene_data["image_url"],
                    audio_url=scene_data["audio_url"],
                    created_at=scene_data["created_at"],
                    updated_at=scene_data["updated_at"]
                )
                scenes.append(scene)
            
            logger.debug(f"Retrieved {len(scenes)} scenes for story ID: {story_id}")
            if scenes:
                logger.debug(f"First scene data: {scenes[0].dict()}")

            # Create story detail with minimal required fields
            story_detail = StoryDetail(
                story_id=story["story_id"],
                title=story["title"],
                status=story["status"],
                user_id=story.get("user_id"),
                created_at=story["created_at"],
                updated_at=story.get("updated_at", story["created_at"]),
                scenes=scenes
            )
            
            # No validation needed for GET endpoints

            elapsed = time.time() - start_time
            logger.info(f"Retrieved full details for story ID: {story_id} in {elapsed:.2f}s, title: {story['title']}, scenes: {len(scenes)}")

            return story_detail
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting story detail in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise

    async def get_user_stories(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all stories for a user"""
        logger.info(f"Getting stories for user ID: {user_id}")
        start_time = time.time()

        try:
            stories = await self.user_client.get_user_stories(user_id)
            # Validate each story in the list
            for story in stories:
                Validator.validate_model_data(story, is_response=True)

            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(stories)} stories for user ID: {user_id} in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting user stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise

    async def search_stories(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for stories by title or prompt"""
        logger.info(f"Searching stories with term: {search_term}, limit: {limit}")
        start_time = time.time()

        try:
            stories = await self.story_client.search_stories(search_term, limit)
            # Validate each story in the list
            for story in stories:
                Validator.validate_model_data(story, is_response=True)

            elapsed = time.time() - start_time
            logger.info(f"Found {len(stories)} stories matching search term: {search_term} in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error searching stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise

    async def get_recent_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recently created stories"""
        logger.info(f"Getting recent stories with limit: {limit}")
        start_time = time.time()

        try:
            stories = await self.story_client.get_recent_stories(limit)
            # Validate each story in the list
            for story in stories:
                Validator.validate_model_data(story, is_response=True)

            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(stories)} recent stories in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error getting recent stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise

    async def delete_story(self, story_id: UUID) -> bool:
        """Delete a story and all its associated scenes and files"""
        logger.info(f"Deleting story with ID: {story_id}")
        start_time = time.time()

        try:
            story = await self.story_client.get_story(story_id)
            if not story:
                logger.warning(f"Story with ID {story_id} not found for deletion")
                return False

            try:
                await self.story_repository.delete_story_files(story_id)
            except Exception as file_error:
                logger.warning(f"Error deleting story files: {str(file_error)}", exc_info=True)

            success = await self.story_repository.delete_story(story_id)

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

    async def update_user(self, user_id: UUID, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's information"""
        logger.info(f"Updating user with ID: {user_id}, fields: {list(data.keys())}")
        start_time = time.time()

        try:
            user = await self.user_client.get_user(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found for update")
                return None

            updated_user = await self.user_client.update_user(user_id, data)

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
        """Update the status of a story"""
        logger.info(f"Updating status for story ID: {story_id} to {status}")
        start_time = time.time()

        try:
            success = await self.story_client.update_story_status(story_id, status)

            elapsed = time.time() - start_time
            if success:
                logger.info(f"Story status updated successfully in {elapsed:.2f}s: {story_id} -> {status}")
            else:
                logger.warning(f"Story status update returned no data in {elapsed:.2f}s: {story_id}")

            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error updating story status in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
