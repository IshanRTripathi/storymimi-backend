from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from uuid import UUID
import logging

from app.models.story import StoryRequest, StoryResponse, StoryDetail, StoryStatus
from app.services.story_service import StoryService

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a router for story endpoints
router = APIRouter(prefix="/stories", tags=["stories"])

# Dependency to get a StoryService instance
async def get_story_service():
    """Dependency to get a StoryService instance"""
    return StoryService()

@router.post("/", response_model=StoryResponse, status_code=202)
async def create_story(request: StoryRequest, service: StoryService = Depends(get_story_service)):
    """Create a new story based on the provided prompt
    
    Args:
        request: The StoryRequest containing story details
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A StoryResponse with the story_id and initial status
        
    Raises:
        HTTPException: If story creation fails
    """
    logger.info(f"Creating new story with title: {request.title}, user_id: {request.user_id}")
    try:
        result = await service.create_new_story(request)
        logger.info(f"Story created successfully with ID: {result['story_id']}")
        return StoryResponse(
            story_id=result["story_id"],
            status=StoryStatus(result["status"])
        )
    except Exception as e:
        logger.error(f"Error creating story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{story_id}", response_model=StoryDetail)
async def get_story(story_id: UUID, service: StoryService = Depends(get_story_service)):
    """Get the full details of a story including all scenes
    
    Args:
        story_id: The ID of the story
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A StoryDetail object with all story information
        
    Raises:
        HTTPException: If story retrieval fails
    """
    logger.info(f"Getting story details for ID: {story_id}")
    try:
        story = await service.get_story_detail(story_id)
        logger.info(f"Successfully retrieved story with ID: {story_id}, title: {story.title}, status: {story.status}")
        return story
    except Exception as e:
        logger.error(f"Error retrieving story with ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{story_id}/status", response_model=Dict[str, Any])
async def get_story_status(story_id: UUID, service: StoryService = Depends(get_story_service)):
    """Get the current status of a story
    
    Args:
        story_id: The ID of the story
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A dictionary with story_id and status
        
    Raises:
        HTTPException: If story retrieval fails
    """
    logger.info(f"Getting status for story ID: {story_id}")
    try:
        status = await service.get_story_status(story_id)
        logger.info(f"Story status for ID {story_id}: {status['status']}")
        return status
    except Exception as e:
        logger.error(f"Error retrieving status for story ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))