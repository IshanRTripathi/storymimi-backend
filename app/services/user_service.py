from typing import Optional
from uuid import UUID
import logging
from pydantic import EmailStr

from app.database.supabase_client import UserRepository, StoryRepository, SceneRepository, StorageService
from app.models.user import User

logger = logging.getLogger(__name__)

class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        story_repo: StoryRepository,
        scene_repo: SceneRepository,
        storage_service: StorageService
    ):
        self.user_repo = user_repo
        self.story_repo = story_repo
        self.scene_repo = scene_repo
        self.storage_service = storage_service

    async def delete_account(self, user_id: UUID, email: EmailStr) -> dict:
        """
        Delete user account and all associated data.
        
        Args:
            user_id: UUID of the user to delete
            email: Email address to validate ownership
            
        Returns:
            dict: Success message or error details
            
        Raises:
            ValueError: If user ID or email is invalid
            Exception: If deletion fails
        """
        try:
            # 1. Validate user exists and email matches
            user = await self.user_repo.get_user(user_id)
            if not user or user.get('email') != email:
                raise ValueError("Invalid user credentials")

            # 2. Get all user's stories
            stories = await self.story_repo.get_user_stories(user_id)
            
            # 3. Delete all scenes for each story
            for story in stories:
                scenes = await self.scene_repo.get_story_scenes(story['story_id'])
                for scene in scenes:
                    await self.scene_repo.delete_scene(scene['scene_id'])
                    
                    # Delete scene media files
                    if scene.get('image_url'):
                        await self.storage_service.delete_file(scene['image_url'])
                    if scene.get('audio_url'):
                        await self.storage_service.delete_file(scene['audio_url'])

            # 4. Delete all stories
            for story in stories:
                await self.story_repo.delete_story(story['story_id'])
                
                # Delete story cover image if exists
                if story.get('cover_image_url'):
                    await self.storage_service.delete_file(story['cover_image_url'])

            # 5. Delete user
            await self.user_repo.delete_user(user_id)

            logger.info(f"Successfully deleted user {user_id} and all associated data")
            return {"message": "Account and all associated data successfully deleted"}

        except ValueError as ve:
            logger.error(f"Validation error during account deletion for {user_id}: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error deleting account for {user_id}: {str(e)}", exc_info=True)
            raise
