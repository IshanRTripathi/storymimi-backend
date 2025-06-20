from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime

from app.database.supabase_client.base_client import SupabaseBaseClient
from app.models.public_story_models import (
    PublicStorySummary,
    PublicStoryDetail,
    StoryCategory,
    AgeRating,
    DifficultyLevel
)
import logging
import time

logger = logging.getLogger(__name__)

class PublicStoriesRepository(SupabaseBaseClient):
    """Repository for public stories"""
    
    def __init__(self):
        """Initialize the repository with a Supabase client instance"""
        super().__init__()
        logger.info("PublicStoriesRepository initialized successfully")
    
    async def get_public_stories(self,
                                category: Optional[StoryCategory] = None,
                                tags: Optional[List[str]] = None,
                                featured: Optional[bool] = None,
                                age_rating: Optional[AgeRating] = None,
                                difficulty: Optional[DifficultyLevel] = None,
                                limit: int = 20,
                                offset: int = 0) -> List[Dict[str, Any]]:
        """Get public stories with optional filtering
        
        Args:
            category: Optional category filter
            tags: Optional list of tags to filter by
            featured: Optional featured flag filter
            age_rating: Optional age rating filter
            difficulty: Optional difficulty level filter
            limit: Maximum number of stories to return
            offset: Offset for pagination
            
        Returns:
            List of public story dictionaries
        """
        start_time = time.time()
        
        query = self.client.table("public_stories").select("*").eq("published", True)
        
        # Apply filters
        if category:
            query = query.eq("category", category.value)
        if tags:
            query = query.or_(f"tags.contains.{tags[0]}")
            for tag in tags[1:]:
                query = query.or_(f"tags.contains.{tag}")
        if featured is not None:
            query = query.eq("featured", featured)
        if age_rating:
            query = query.eq("age_rating", age_rating.value)
        if difficulty:
            query = query.eq("difficulty_level", difficulty.value)
        
        # Add ordering and pagination
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        
        try:
            response = await query.execute()
            stories = response.data if response.data else []
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(stories)} public stories in {elapsed:.2f}s")
            return stories
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get public stories in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_public_story(self, story_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a specific public story by ID
        
        Args:
            story_id: The ID of the story to retrieve
            
        Returns:
            The story dictionary or None if not found
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        try:
            response = await self.client.table("public_stories").select("*").eq("id", story_id_str).eq("published", True).execute()
            story = response.data[0] if response.data else None
            
            elapsed = time.time() - start_time
            if story:
                logger.info(f"Retrieved public story {story_id_str} in {elapsed:.2f}s")
            else:
                logger.info(f"Public story {story_id_str} not found")
            
            return story
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get public story {story_id_str} in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def increment_view_count(self, story_id: Union[str, UUID]) -> bool:
        """Increment the view count for a public story
        
        Args:
            story_id: The ID of the story
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        try:
            response = await self.client.table("public_stories").update({"view_count": "view_count + 1"}).eq("id", story_id_str).eq("published", True).execute()
            success = bool(response.data)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"Incremented view count for story {story_id_str} in {elapsed:.2f}s")
            else:
                logger.warning(f"Failed to increment view count for story {story_id_str}")
            
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to increment view count for story {story_id_str} in {elapsed:.2f}s: {str(e)}", exc_info=True)
            return False
