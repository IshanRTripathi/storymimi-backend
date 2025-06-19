from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.models.user import User, UserCreate, UserResponse, UserStoriesResponse
from app.services.story_service import StoryService
from app.database.supabase_client import UserRepository

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a router for user endpoints
router = APIRouter(prefix="/users", tags=["users"])

# Dependency to get a SupabaseClient instance
async def get_user_repository() -> UserRepository:
    """Dependency to get a UserRepository instance"""
    return UserRepository()

# Dependency to get a StoryService instance
async def get_story_service() -> StoryService:
    """Dependency to get a StoryService instance"""
    return StoryService()

@router.post("/", response_model=UserResponse, status_code=201, tags=["users"], summary="Create User", description="Create a new user.")
async def create_user(
    user: UserCreate = Body(..., example={"email": "user@example.com", "username": "user123"}),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Create a new user and return user details."""
    logger.info(f"Creating new user with username: {user.username}, email: {user.email}")
    try:
        result = await user_repo.create_user(user.email, user.username)
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

@router.get("/{user_id}", response_model=UserResponse, tags=["users"], summary="Get User", description="Get a user by ID.")
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get a user by their unique ID."""
    logger.info(f"Getting user with ID: {user_id}")
    try:
        user = await user_repo.get_user(user_id)
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

@router.get("/{user_id}/stories", response_model=List[Dict[str, Any]], tags=["users"], summary="Get User Stories", description="Get all stories for a user.")
async def get_user_stories(
    user_id: UUID,
    service: StoryService = Depends(get_story_service)
):
    """Get all stories for a user by user ID."""
    logger.info(f"Getting stories for user ID: {user_id}")
    try:
        stories = await service.get_user_stories(user_id)
        logger.info(f"Retrieved {len(stories)} stories for user ID: {user_id}")
        return stories
    except Exception as e:
        logger.error(f"Error retrieving stories for user ID {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class UserUpdateModel(UserCreate):
    """Model for updating a user (all fields optional except user_id)"""
    email: Optional[str] = None
    username: Optional[str] = None

@router.patch("/{user_id}", response_model=UserResponse, tags=["users"], summary="Update User", description="Update a user's information.")
async def update_user(
    user_id: UUID,
    user_data: UserUpdateModel = Body(..., example={"email": "new@example.com", "username": "newname"}),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Update a user's information by user ID."""
    logger.info(f"Updating user with ID: {user_id}, fields: {user_data.dict(exclude_unset=True)}")
    try:
        update_fields = user_data.dict(exclude_unset=True)
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields provided for update.")
        if "user_id" in update_fields:
            logger.warning(f"Attempted to update user_id for user {user_id}")
            raise HTTPException(status_code=400, detail="Cannot update user_id field")
        updated_user = await user_repo.update_user(user_id, update_fields)
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