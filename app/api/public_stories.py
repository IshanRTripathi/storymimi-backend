from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.public_story_models import (
    PublicStorySummary,
    PublicStoryDetail,
    StoryCategory,
    AgeRating,
    DifficultyLevel
)
from app.services.public_story_service import PublicStoryService
from app.database.supabase_client.public_stories_client import PublicStoriesRepository

router = APIRouter(prefix="/public-stories", tags=["public-stories"])

def get_public_story_service(
    repo: PublicStoriesRepository = Depends(PublicStoriesRepository)
) -> PublicStoryService:
    """Dependency to get a PublicStoryService instance"""
    return PublicStoryService(repo)

@router.get("/", response_model=List[PublicStorySummary], tags=["public-stories"],
            summary="Get Public Stories",
            description="Get a list of public stories with optional filtering")
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

@router.get("/{story_id}", response_model=PublicStoryDetail, tags=["public-stories"],
            summary="Get Public Story by ID",
            description="Get a specific public story by ID")
async def get_public_story(
    story_id: UUID,
    service: PublicStoryService = Depends(get_public_story_service)
) -> PublicStoryDetail:
    """Get a specific public story by ID"""
    try:
        story = await service.get_public_story(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        return story
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
