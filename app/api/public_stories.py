from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import UUID
import logging

# Create a logger for this module
logger = logging.getLogger(__name__)

from app.models.public_story_models import (
    PublicStorySummary,
    PublicStoryDetail,
    StoryCategory,
    AgeRating,
    DifficultyLevel,
    CategorizedPublicStories
)
from app.services.public_story_service import PublicStoryService
from app.database.supabase_client.public_stories_client import PublicStoriesRepository

router = APIRouter(prefix="/stories/public", tags=["public-stories"])

def get_public_story_service(
    repo: PublicStoriesRepository = Depends(PublicStoriesRepository)
) -> PublicStoryService:
    """Dependency to get a PublicStoryService instance"""
    return PublicStoryService(repo)

@router.get(
    "/categorized",
    response_model=CategorizedPublicStories,
    tags=["public-stories"],
    summary="Get Categorized Public Stories",
    description="""
    Get public stories grouped by category. Each category contains a list of stories with basic information.
    
    Response includes:
    - List of all available categories
    - Stories grouped by their category
    - Each story includes title, description, cover image, tags, duration, and other metadata
    
    Example response:
    ```json
    {
        "categories": ["adventure", "fantasy", "animals"],
        "stories": {
            "adventure": [
                {
                    "id": "063f9edc-07ca-499f-9793-a1ce4c7db763",
                    "title": "The Magical Forest",
                    "description": "A story about a girl's adventure in a magical forest",
                    "cover_image_url": "https://example.com/images/story1.jpg",
                    "tags": ["magic", "forest", "adventure"],
                    "duration": "3 minutes",
                    "featured": true,
                    "age_rating": "ALL",
                    "category": "adventure",
                    "difficulty_level": "beginner",
                    "created_at": "2025-06-20T10:25:47.000000+05:30",
                    "updated_at": "2025-06-20T10:25:47.000000+05:30"
                }
            ]
        }
    }
    ```
    
    Available categories:
    - adventure
    - fantasy
    - science-fiction
    - friendship
    - animals
    - mystery
    - educational
    """
)
async def get_categorized_stories(
    service: PublicStoryService = Depends(get_public_story_service)
) -> CategorizedPublicStories:
    """Get public stories grouped by category"""
    try:
        categorized_stories = await service.get_categorized_stories()
        return categorized_stories
    except Exception as e:
        logger.error(f"Error getting categorized stories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{story_id}",
    response_model=PublicStoryDetail,
    tags=["public-stories"],
    summary="Get Public Story Details",
    description="""
    Get detailed information about a specific public story by its ID.
    
    Response includes:
    - Complete story metadata
    - All scenes with text, images, and audio
    - View count
    - Age rating and difficulty level
    
    Example response:
    ```json
    {
        "id": "063f9edc-07ca-499f-9793-a1ce4c7db763",
        "title": "The Magical Forest",
        "description": "A story about a girl's adventure in a magical forest",
        "cover_image_url": "https://example.com/images/story1.jpg",
        "tags": ["magic", "forest", "adventure"],
        "duration": "3 minutes",
        "featured": true,
        "view_count": 123,
        "age_rating": "ALL",
        "category": "adventure",
        "difficulty_level": "beginner",
        "created_at": "2025-06-20T10:25:47.000000+05:30",
        "updated_at": "2025-06-20T10:25:47.000000+05:30",
        "published": true,
        "scenes": [
            {
                "sequence": 0,
                "text": "Once upon a time, a curious girl named Luna discovered a hidden path...",
                "image_url": "https://example.com/images/story1_scene0.png",
                "audio_url": "https://example.com/audio/story1_scene0.mp3"
            },
            {
                "sequence": 1,
                "text": "As Luna stepped into the magical forest...",
                "image_url": "https://example.com/images/story1_scene1.png",
                "audio_url": "https://example.com/audio/story1_scene1.mp3"
            }
        ]
    }
    ```
    """
)
async def get_story_details(
    story_id: UUID,
    service: PublicStoryService = Depends(get_public_story_service)
) -> PublicStoryDetail:
    """Get detailed information about a public story"""
    try:
        story = await service.get_story_details(story_id)
        if not story:
            logger.warning(f"Story not found: {story_id}")
            raise HTTPException(status_code=404, detail="Story not found")
        logger.info(f"Retrieved story details for ID: {story_id}")
        return story
    except Exception as e:
        logger.error(f"Error getting story details for ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
@router.get(
    "",
    response_model=List[PublicStorySummary],
    tags=["public-stories"],
    summary="Get Public Stories",
    description="Get a list of public stories with optional filtering"
)
async def get_public_stories(
    category: Optional[StoryCategory] = None,
    tags: Optional[List[str]] = None,
    featured: Optional[bool] = None,
    age_rating: Optional[AgeRating] = None,
    difficulty: Optional[DifficultyLevel] = None,
    limit: int = 20,
    offset: int = 0,
    service: PublicStoryService = Depends(get_public_story_service)
) -> List[PublicStorySummary]:
    """Get public stories with optional filtering"""
    try:
        stories = await service.get_public_stories(
            category=category,
            tags=tags,
            featured=featured,
            age_rating=age_rating,
            difficulty=difficulty,
            limit=limit,
            offset=offset
        )
        return stories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


