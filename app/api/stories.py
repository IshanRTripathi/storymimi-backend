from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List
from uuid import UUID
import logging

from app.database.supabase_client import SupabaseClient
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
        
@router.put("/{story_id}/status", response_model=Dict[str, bool])
async def update_story_status(
    story_id: UUID, 
    status_data: Dict[str, str], 
    service: StoryService = Depends(get_story_service)
):
    """Update the status of a story
    
    Args:
        story_id: The ID of the story
        status_data: Dictionary with the new status value
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A dictionary with success status
        
    Raises:
        HTTPException: If status update fails
    """
    logger.info(f"Updating status for story ID: {story_id}")
    try:
        # Validate that we have a status field
        if "status" not in status_data:
            logger.warning(f"Missing status field in request for story {story_id}")
            raise HTTPException(status_code=400, detail="Missing status field in request")
            
        # Validate that the status is valid
        try:
            new_status = StoryStatus(status_data["status"])
        except ValueError:
            valid_statuses = [s.value for s in StoryStatus]
            logger.warning(f"Invalid status value: {status_data['status']} for story {story_id}. Valid values: {valid_statuses}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status value. Valid values: {valid_statuses}"
            )
            
        # Update the story status
        success = await service.update_story_status(story_id, new_status)
        if not success:
            logger.warning(f"Story with ID {story_id} not found for status update")
            raise HTTPException(status_code=404, detail=f"Story with ID {story_id} not found")
            
        logger.info(f"Story status updated successfully: {story_id} -> {new_status.value}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status for story ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/", response_model=List[Dict[str, Any]])
async def search_stories(
    q: str = Query(..., description="Search term to look for in story titles and prompts"),
    limit: int = Query(10, description="Maximum number of results to return", ge=1, le=50),
    service: StoryService = Depends(get_story_service)
):
    """Search for stories by title or prompt
    
    Args:
        q: The search term to look for in titles and prompts
        limit: Maximum number of results to return (default: 10, max: 50)
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A list of story dictionaries matching the search term
        
    Raises:
        HTTPException: If search fails
    """
    logger.info(f"Searching stories with term: {q}, limit: {limit}")
    try:
        stories = await service.search_stories(q, limit)
        logger.info(f"Found {len(stories)} stories matching search term: {q}")
        return stories
    except Exception as e:
        logger.error(f"Error searching stories with term {q}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent/", response_model=List[Dict[str, Any]])
async def get_recent_stories(
    limit: int = Query(10, description="Maximum number of stories to return", ge=1, le=50),
    service: StoryService = Depends(get_story_service)
):
    """Get the most recently created stories
    
    Args:
        limit: Maximum number of stories to return (default: 10, max: 50)
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A list of recent story dictionaries
        
    Raises:
        HTTPException: If retrieval fails
    """
    logger.info(f"Getting recent stories with limit: {limit}")
    try:
        stories = await service.get_recent_stories(limit)
        logger.info(f"Retrieved {len(stories)} recent stories")
        return stories
    except Exception as e:
        logger.error(f"Error getting recent stories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{story_id}", response_model=Dict[str, bool])
async def delete_story(story_id: UUID, service: StoryService = Depends(get_story_service)):
    """Delete a story and all its associated scenes and files
    
    Args:
        story_id: The ID of the story to delete
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A dictionary with success status
        
    Raises:
        HTTPException: If deletion fails
    """
    logger.info(f"Deleting story with ID: {story_id}")
    try:
        success = await service.delete_story(story_id)
        if not success:
            logger.warning(f"Story with ID {story_id} not found for deletion")
            raise HTTPException(status_code=404, detail=f"Story with ID {story_id} not found")
            
        logger.info(f"Story deleted successfully: {story_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting story with ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))