from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from app.models.public_story_models import (
    PublicStorySummary,
    PublicStoryDetail,
    PublicStoryScene,
    CategorizedPublicStories,
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
    
    async def get_story_details(self, story_id: Union[str, UUID]) -> Optional[PublicStoryDetail]:
        """Get detailed information about a public story
        
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
                **story
            )
            

            
            return story_detail
        except Exception as e:
            logger.error(f"Error getting story details {story_id}: {str(e)}", exc_info=True)
            raise

    async def get_categorized_stories(self) -> CategorizedPublicStories:
        """Get public stories grouped by category
        
        Returns:
            CategorizedPublicStories object with stories grouped by category
        """
        try:
            # Get all stories
            stories = await self.repo.get_public_stories()
            
            # Group stories by category
            categorized_stories = {}
            for story in stories:
                category = story.get("category", StoryCategory.ADVENTURE.value)
                if category not in categorized_stories:
                    categorized_stories[category] = []
                categorized_stories[category].append(PublicStorySummary(**story))
            
            # Get all unique categories
            categories = list(categorized_stories.keys())
            
            return CategorizedPublicStories(
                categories=categories,
                stories=categorized_stories
            )
        except Exception as e:
            logger.error(f"Error getting categorized stories: {str(e)}", exc_info=True)
            raise
            