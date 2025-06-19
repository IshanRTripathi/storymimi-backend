from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, List
from uuid import UUID
import logging
import uuid
from datetime import datetime

from app.database.supabase_client import StoryRepository, SceneRepository, StorageService
from app.models.story_types import StoryRequest, StoryResponse, StoryDetail, StoryStatus
from app.services.story_service import StoryService
from app.utils.json_converter import JSONConverter
from app.utils.validator import Validator

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a router for story endpoints
router = APIRouter(prefix="/stories", tags=["stories"])

# Dependency to get a StoryService instance
def get_story_service(db_client: StoryRepository = Depends(StoryRepository)) -> StoryService:
    """Dependency to get a StoryService instance"""
    return StoryService(db_client)

@router.post("/", response_model=StoryResponse, status_code=202, tags=["stories"], summary="Create Story", description="Create a new story based on the provided prompt.")
async def create_story(
    request: StoryRequest = Body(..., example={"title": "My Story", "prompt": "A magical adventure", "user_id": "uuid-here"}),
    service: StoryService = Depends(get_story_service)
):
    """Create a new story based on the provided prompt."""
    logger.info(f"Creating new story with title: {request.title}, user_id: {request.user_id}")
    try:
        # Validate the request data as a request object
        result = await service.create_new_story(request)
        
        # Validate model data before database operations
        Validator.validate_model_data(result, is_initial_creation=True)
        
        logger.info(f"Story created successfully with ID: {result['story_id']}")
        response = JSONConverter.parse_json(result, StoryResponse)
        return response
    except Exception as e:
        logger.error(f"Error creating story: {str(e)}", exc_info=True)
        # Generate a UUID for the error response
        error_uuid = str(uuid.uuid4())
        
        error_response = StoryResponse(
            story_id=error_uuid,
            status=StoryStatus.FAILED,
            title="Error",
            user_id=request.user_id,
            created_at=datetime.now()
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "story_id": str(error_uuid),
                "status": StoryStatus.FAILED,
                "title": "Error",
                "created_at": datetime.now().isoformat()
            }
        )

@router.get("/{story_id}", response_model=StoryDetail, tags=["stories"], summary="Get Story", description="Get the full details of a story including all scenes.")
async def get_story(
    story_id: UUID,
    service: StoryService = Depends(get_story_service)
):
    """Get the full details of a story including all scenes."""
    logger.info(f"Getting story details for ID: {story_id}")
    try:
        story = await service.get_story_detail(story_id)
        logger.info(f"Successfully retrieved story with ID: {story_id}, title: {story.title}, status: {story.status}")
        
        # Validate the story data as a response object
        StoryValidator.validate_story_data(story.dict())
        return story
    except Exception as e:
        logger.error(f"Error retrieving story with ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{story_id}/status", response_model=Dict[str, Any], tags=["stories"], summary="Get Story Status", description="Get the current status of a story.")
async def get_story_status(
    story_id: UUID,
    service: StoryService = Depends(get_story_service)
):
    """Get the current status of a story."""
    logger.info(f"Getting status for story ID: {story_id}")
    try:
        status = await service.get_story_status(story_id)
        logger.info(f"Story status for ID {story_id}: {status['status']}")
        return status
    except Exception as e:
        logger.error(f"Error retrieving status for story ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
        
@router.put("/{story_id}/status", response_model=Dict[str, bool], tags=["stories"], summary="Update Story Status", description="Update the status of a story.")
async def update_story_status(
    story_id: UUID,
    status_data: Dict[str, str] = Body(..., example={"status": "completed"}),
    service: StoryService = Depends(get_story_service)
):
    """Update the status of a story."""
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
            
        logger.info(f"Story status updated successfully: {story_id} -> {new_status}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating status for story ID {story_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/", response_model=List[Dict[str, Any]], tags=["stories"], summary="Search Stories", description="Search for stories by title or prompt.")
async def search_stories(
    q: str = Query(..., description="Search term to look for in story titles and prompts"),
    limit: int = Query(10, description="Maximum number of results to return", ge=1, le=50),
    service: StoryService = Depends(get_story_service)
):
    """Search for stories by title or prompt."""
    logger.info(f"Searching stories with term: {q}, limit: {limit}")
    try:
        stories = await service.search_stories(q, limit)
        logger.info(f"Found {len(stories)} stories matching search term: {q}")
        return stories
    except Exception as e:
        logger.error(f"Error searching stories with term {q}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent/", response_model=List[Dict[str, Any]], tags=["stories"], summary="Get Recent Stories", description="Get the most recently created stories.")
async def get_recent_stories(
    limit: int = Query(10, description="Maximum number of stories to return", ge=1, le=50),
    service: StoryService = Depends(get_story_service)
):
    """Get the most recently created stories."""
    logger.info(f"Getting recent stories with limit: {limit}")
    try:
        stories = await service.get_recent_stories(limit)
        logger.info(f"Retrieved {len(stories)} recent stories")
        return stories
    except Exception as e:
        logger.error(f"Error getting recent stories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{story_id}", response_model=Dict[str, bool], tags=["stories"], summary="Delete Story", description="Delete a story and all its associated scenes and files.")
async def delete_story(
    story_id: UUID,
    service: StoryService = Depends(get_story_service)
):
    """Delete a story and all its associated scenes and files."""
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