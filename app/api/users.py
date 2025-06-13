from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from uuid import UUID
import logging

from app.models.user import User, UserCreate, UserResponse, UserStoriesResponse
from app.services.story_service import StoryService
from app.database.supabase_client import SupabaseClient

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a router for user endpoints
router = APIRouter(prefix="/users", tags=["users"])

# Dependency to get a SupabaseClient instance
async def get_db_client():
    """Dependency to get a SupabaseClient instance"""
    return SupabaseClient()

# Dependency to get a StoryService instance
async def get_story_service():
    """Dependency to get a StoryService instance"""
    return StoryService()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db_client: SupabaseClient = Depends(get_db_client)):
    """Create a new user
    
    Args:
        user: The UserCreate object with user details
        db_client: The SupabaseClient instance (injected by FastAPI)
        
    Returns:
        A UserResponse with the created user details
        
    Raises:
        HTTPException: If user creation fails
    """
    logger.info(f"Creating new user with username: {user.username}, email: {user.email}")
    try:
        result = await db_client.create_user(user.email, user.username)
        logger.debug(f"User creation result: {result}")
        if not result:
            logger.error("Failed to create user: No result returned from database")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        logger.info(f"User created successfully with ID: {result['user_id']}")
        return UserResponse(
            user_id=result["user_id"],
            email=result["email"],
            username=result["username"],
            created_at=result["created_at"]
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db_client: SupabaseClient = Depends(get_db_client)):
    """Get a user by ID
    
    Args:
        user_id: The ID of the user
        db_client: The SupabaseClient instance (injected by FastAPI)
        
    Returns:
        A UserResponse with the user details
        
    Raises:
        HTTPException: If user retrieval fails
    """
    logger.info(f"Getting user with ID: {user_id}")
    try:
        user = await db_client.get_user(user_id)
        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        logger.info(f"Successfully retrieved user with ID: {user_id}, username: {user['username']}")
        return UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            username=user["username"],
            created_at=user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user with ID {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/stories", response_model=List[Dict[str, Any]])
async def get_user_stories(user_id: UUID, service: StoryService = Depends(get_story_service)):
    """Get all stories for a user
    
    Args:
        user_id: The ID of the user
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        A list of story dictionaries
        
    Raises:
        HTTPException: If story retrieval fails
    """
    logger.info(f"Getting stories for user ID: {user_id}")
    try:
        stories = await service.get_user_stories(user_id)
        logger.info(f"Retrieved {len(stories)} stories for user ID: {user_id}")
        return stories
    except Exception as e:
        logger.error(f"Error retrieving stories for user ID {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID, 
    user_data: Dict[str, Any], 
    service: StoryService = Depends(get_story_service)
):
    """Update a user's information
    
    Args:
        user_id: The ID of the user to update
        user_data: Dictionary of fields to update
        service: The StoryService instance (injected by FastAPI)
        
    Returns:
        The updated UserResponse
        
    Raises:
        HTTPException: If user update fails
    """
    logger.info(f"Updating user with ID: {user_id}, fields: {list(user_data.keys())}")
    try:
        # Validate that we're not trying to update the user_id
        if "user_id" in user_data:
            logger.warning(f"Attempted to update user_id for user {user_id}")
            raise HTTPException(status_code=400, detail="Cannot update user_id field")
            
        updated_user = await service.update_user(user_id, user_data)
        if not updated_user:
            logger.warning(f"User with ID {user_id} not found for update")
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        logger.info(f"User updated successfully: {user_id}")
        return UserResponse(
            user_id=updated_user["user_id"],
            email=updated_user["email"],
            username=updated_user["username"],
            created_at=updated_user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user with ID {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))