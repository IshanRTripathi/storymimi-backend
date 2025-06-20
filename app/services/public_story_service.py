from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from app.models.public_story_models import (
    PublicStorySummary,
    PublicStoryDetail,
    StoryCategory,
    AgeRating,
    DifficultyLevel
)
from app.database.supabase_client.public_stories_client import PublicStoriesRepository
import logging

logger = logging.getLogger(__name__)

class PublicStoryService:
    """Service for handling public stories"""
    
    def __init__(self, repo: PublicStoriesRepository):
        self.repo = repo
    
    async def get_public_stories(self,
                                category: Optional[StoryCategory] = None,
                                tags: Optional[List[str]] = None,
                                featured: Optional[bool] = None,
                                age_rating: Optional[AgeRating] = None,
                                difficulty: Optional[DifficultyLevel] = None,
                                limit: int = 20,
                                offset: int = 0) -> List[PublicStorySummary]:
        """Get public stories with optional filtering
        
        Args:
            Same as repository method
            
        Returns:
            List of PublicStorySummary objects
        """
        try:
            stories = await self.repo.get_public_stories(
                category=category,
                tags=tags,
                featured=featured,
                age_rating=age_rating,
                difficulty=difficulty,
                limit=limit,
                offset=offset
            )
            
            return [PublicStorySummary(**story) for story in stories]
        except Exception as e:
            logger.error(f"Error getting public stories: {str(e)}", exc_info=True)
            raise
    
    async def get_public_story(self, story_id: Union[str, UUID]) -> Optional[PublicStoryDetail]:
        """Get a specific public story by ID
        
        Args:
            story_id: The ID of the story
            
        Returns:
            PublicStoryDetail object or None if not found
        """
        try:
            story = await self.repo.get_public_story(story_id)
            if not story:
                return None
                
            # Convert scenes JSON to list of PublicStoryScene objects
            scenes = []
            if story.get("scenes"):
                for scene_data in story["scenes"]:
                    scenes.append(PublicStoryScene(**scene_data))
            
            # Create PublicStoryDetail object
            story_detail = PublicStoryDetail(
                **story,
                scenes=scenes,
                id=story["id"]
            )
            
            # Increment view count
            await self.repo.increment_view_count(story_id)
            
            return story_detail
        except Exception as e:
            logger.error(f"Error getting public story {story_id}: {str(e)}", exc_info=True)
            raise
