from fastapi import APIRouter, HTTPException, Depends, Query, Body, BackgroundTasks
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.models.story_types import StoryRequest, StoryResponse, StoryDetail, StoryStatus, Scene
from app.services.story_service import StoryService
from app.services.ai_service import AIService
from app.services.elevenlabs_service import ElevenLabsService
from app.database.supabase_client import StoryRepository, SceneRepository, UserRepository, StorageService
from app.utils.json_converter import JSONConverter
from app.utils.validator import Validator

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a router for story endpoints
router = APIRouter(prefix="/stories", tags=["stories"])

# Dependency to get a StoryService instance
async def get_story_service(
    story_client: StoryRepository = Depends(StoryRepository),
    scene_client: SceneRepository = Depends(SceneRepository),
    user_client: UserRepository = Depends(UserRepository)
) -> StoryService:
    """Dependency to get a StoryService instance"""
    return StoryService(story_client, scene_client, user_client)

# Dependency to get an AIService instance
async def get_ai_service() -> AIService:
    """Dependency to get an AIService instance"""
    return AIService()

# Dependency to get an ElevenLabsService instance
async def get_elevenlabs_service() -> ElevenLabsService:
    """Dependency to get an ElevenLabsService instance"""
    return ElevenLabsService()

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
        
        # Parse datetime strings to datetime objects if they are strings
        created_at = result["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        updated_at = result["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        # Create StoryResponse directly from the result
        response = StoryResponse(
            status=result["status"],
            title=result["title"],
            story_id=result["story_id"],
            user_id=result["user_id"],
            created_at=created_at,
            updated_at=updated_at,
            error=None
        )
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
        
        # No validation needed for GET endpoints
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

@router.post("/conversation-tracking", response_model=Dict[str, Any], tags=["stories"], summary="Track Conversation Completion", description="Track conversation completion and optionally create a story from the conversation data.")
async def track_conversation_completion(
    background_tasks: BackgroundTasks,
    conversation_data: Dict[str, Any] = Body(..., example={
        "user_id": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
        "conversation_id": "conv_01jy8c468pegdakjm96v30brac",
        "completed_at": "2025-06-21T10:05:05.417792",
        "user_type": "authenticated",
        "platform": "flutter_app",
        "metrics": {
            "duration_seconds": 175,
            "duration_minutes": 2,
            "total_messages": 21,
            "user_messages": 10,
            "agent_messages": 11,
            "avg_response_time": 8.33,
            "agent_id": "agent_01jy5rtdqtec3vtc4xtjbqkjrv",
            "platform": "flutter_elevenlabs",
            "audio_chunks_processed": 0
        },
        "conversation_duration": "0:02:55.487360",
        "firebase_uid": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
        "user_email": "cursordemo249@gmail.com",
        "user_display_name": ""
    }),
    story_service: StoryService = Depends(get_story_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """Track conversation completion and optionally create a story from the conversation data.
    
    Args:
        conversation_data: Conversation tracking data from Flutter app
        background_tasks: FastAPI background tasks
        story_service: StoryService instance
        ai_service: AIService instance
        
    Returns:
        Dict containing tracking status and optional story creation info
    """
    logger.info(f"Tracking conversation completion: {conversation_data.get('conversation_id')}")
    
    try:
        # Extract required fields
        user_id = conversation_data.get("user_id")
        conversation_id = conversation_data.get("conversation_id")
        completed_at = conversation_data.get("completed_at")
        metrics = conversation_data.get("metrics", {})
        
        if not all([user_id, conversation_id, completed_at]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: user_id, conversation_id, completed_at"
            )
        
        # Log the conversation tracking data
        logger.info(f"Conversation tracked successfully: {conversation_id} for user: {user_id}")
        logger.info(f"Conversation metrics: {metrics}")
        
        # Store conversation tracking data (you might want to save this to a database)
        tracking_result = {
            "status": "tracked",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "completed_at": completed_at,
            "metrics": metrics,
            "message": "Conversation completion tracked successfully"
        }
        
        # Optionally create a story from the conversation
        # This could be done immediately or in the background
        if conversation_data.get("create_story", False):
            # Add background task to create story from conversation
            background_tasks.add_task(
                create_story_from_conversation,
                conversation_data,
                story_service,
                ai_service
            )
            tracking_result["story_creation"] = "scheduled"
        
        return tracking_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "TRACKING_ERROR"}
        )

async def create_story_from_conversation(
    conversation_data: Dict[str, Any],
    story_service: StoryService,
    ai_service: AIService
):
    """Create a story from conversation data using AI processing.
    
    Args:
        conversation_data: Conversation tracking data
        story_service: StoryService instance
        ai_service: AIService instance
    """
    try:
        user_id = conversation_data.get("user_id")
        conversation_id = conversation_data.get("conversation_id")
        metrics = conversation_data.get("metrics", {})
        
        logger.info(f"Creating story from conversation: {conversation_id}")
        
        # Generate a title and prompt from the conversation data
        title = f"Conversation Story - {conversation_id[:8]}"
        
        # Create a prompt based on conversation metrics
        prompt = f"""
        Create a story based on a conversation with the following characteristics:
        - Duration: {metrics.get('duration_minutes', 0)} minutes
        - Total messages: {metrics.get('total_messages', 0)}
        - User messages: {metrics.get('user_messages', 0)}
        - Agent messages: {metrics.get('agent_messages', 0)}
        - Average response time: {metrics.get('avg_response_time', 0)} seconds
        - Agent ID: {metrics.get('agent_id', 'unknown')}
        
        Please create an engaging story that captures the essence of this conversation.
        """
        
        # Create story request
        story_request = StoryRequest(
            title=title,
            prompt=prompt,
            user_id=user_id
        )
        
        # Create the story using the existing story service
        result = await story_service.create_new_story(story_request)
        
        logger.info(f"Story created from conversation {conversation_id}: {result.get('story_id')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating story from conversation {conversation_id}: {str(e)}", exc_info=True)
        # Don't raise here as this is a background task

@router.post("/conversation-to-story", response_model=Dict[str, Any], tags=["stories"], summary="Create Story from ElevenLabs Conversation", description="Fetch conversation transcript from ElevenLabs and create a story from the actual conversation content.")
async def create_story_from_elevenlabs_conversation(
    background_tasks: BackgroundTasks,
    conversation_request: Dict[str, Any] = Body(..., example={
        "conversation_id": "conv_01jy8c468pegdakjm96v30brac",
        "user_id": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
        "agent_id": "agent_01jy5rtdqtec3vtc4xtjbqkjrv",
        "fetch_transcript": True,
        "story_title": "My Conversation Story",
        "story_prompt": "Create a story based on this conversation"
    }),
    story_service: StoryService = Depends(get_story_service),
    ai_service: AIService = Depends(get_ai_service),
    elevenlabs_service: ElevenLabsService = Depends(get_elevenlabs_service)
):
    """Create a story from ElevenLabs conversation by fetching the transcript.
    
    Args:
        conversation_request: Request containing conversation details
        background_tasks: FastAPI background tasks
        story_service: StoryService instance
        ai_service: AIService instance
        elevenlabs_service: ElevenLabsService instance
        
    Returns:
        Dict containing story creation status
    """
    logger.info(f"Creating story from ElevenLabs conversation: {conversation_request.get('conversation_id')}")
    
    try:
        conversation_id = conversation_request.get("conversation_id")
        user_id = conversation_request.get("user_id")
        agent_id = conversation_request.get("agent_id")
        fetch_transcript = conversation_request.get("fetch_transcript", True)
        
        if not all([conversation_id, user_id]):
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: conversation_id, user_id"
            )
        
        # Add background task to fetch transcript and create story
        background_tasks.add_task(
            process_elevenlabs_conversation,
            conversation_request,
            story_service,
            ai_service,
            elevenlabs_service
        )
        
        return {
            "status": "processing",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "message": "Story creation from conversation transcript has been scheduled",
            "fetch_transcript": fetch_transcript,
            "elevenlabs_available": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling story creation from conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "STORY_CREATION_ERROR"}
        )

async def process_elevenlabs_conversation(
    conversation_request: Dict[str, Any],
    story_service: StoryService,
    ai_service: AIService,
    elevenlabs_service: ElevenLabsService
):
    """Process ElevenLabs conversation to create a story.
    
    Args:
        conversation_request: Request containing conversation details
        story_service: StoryService instance
        ai_service: AIService instance
        elevenlabs_service: ElevenLabsService instance
    """
    try:
        conversation_id = conversation_request.get("conversation_id")
        user_id = conversation_request.get("user_id")
        agent_id = conversation_request.get("agent_id")
        fetch_transcript = conversation_request.get("fetch_transcript", True)
        custom_title = conversation_request.get("story_title")
        custom_prompt = conversation_request.get("story_prompt")
        
        logger.info(f"Processing ElevenLabs conversation: {conversation_id}")
        
        # Fetch conversation transcript from ElevenLabs
        transcript = None
        if fetch_transcript:
            transcript = await elevenlabs_service.get_conversation_transcript(conversation_id, agent_id)
            if transcript:
                logger.info(f"Successfully fetched transcript for conversation: {conversation_id}")
            else:
                logger.warning(f"Could not fetch transcript for conversation: {conversation_id}")
        
        # Generate title and prompt
        title = custom_title or f"Conversation Story - {conversation_id[:8]}"
        
        if transcript:
            # Use actual transcript content
            prompt = f"""
            Create a story based on the following conversation transcript:
            
            {transcript}
            
            Please create an engaging story that captures the essence and key moments of this conversation.
            """
        else:
            # Use conversation metadata
            prompt = custom_prompt or f"""
            Create a story based on a conversation with ID: {conversation_id}
            Agent ID: {agent_id}
            User ID: {user_id}
            
            Please create an engaging story that could have emerged from this conversation.
            """
        
        # Create story request
        story_request = StoryRequest(
            title=title,
            prompt=prompt,
            user_id=user_id
        )
        
        # Create the story using the existing story service
        result = await story_service.create_new_story(story_request)
        
        logger.info(f"Story created from ElevenLabs conversation {conversation_id}: {result.get('story_id')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing ElevenLabs conversation {conversation_id}: {str(e)}", exc_info=True)
        # Don't raise here as this is a background task