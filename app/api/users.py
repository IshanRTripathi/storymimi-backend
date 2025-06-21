from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.models.user import User, UserCreate, UserResponse
from app.services.story_service import StoryService
from app.services.user_service import UserService
from app.database.supabase_client import StorageService
from app.database.supabase_client import UserRepository, StoryRepository, SceneRepository
from app.utils.validator import Validator

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a router for user endpoints
router = APIRouter(prefix="/users", tags=["users"])

# Dependency to get a SupabaseClient instance
async def get_user_repository() -> UserRepository:
    """Dependency to get a UserRepository instance"""
    return UserRepository()

# Dependency to get a StoryService instance
async def get_user_service(
    user_repo: UserRepository = Depends(UserRepository),
    story_repo: StoryRepository = Depends(StoryRepository),
    scene_repo: SceneRepository = Depends(SceneRepository),
    storage_service: StorageService = Depends(StorageService)
) -> UserService:
    """Dependency to get a UserService instance"""
    return UserService(user_repo, story_repo, scene_repo, storage_service)

async def get_story_service(
    story_client: StoryRepository = Depends(StoryRepository),
    scene_client: SceneRepository = Depends(SceneRepository),
    user_client: UserRepository = Depends(UserRepository)
) -> StoryService:
    """Dependency to get a StoryService instance"""
    return StoryService(story_client, scene_client, user_client)

@router.get("/{user_id}", response_model=UserResponse, tags=["users"], summary="Get User", description="Check if a user exists by their Firebase UID.")
async def get_user(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get user details by their Firebase UID.
    
    Args:
        user_id: Firebase user ID
        user_repo: User repository instance
        
    Returns:
        UserResponse: User details if found
        
    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if database error occurs
    """
    logger.info(f"Checking if user exists with Firebase UID: {user_id}")
    try:
        user = await user_repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"error_code": "USER_NOT_FOUND"}
            )
        
        logger.info(f"User found with Firebase UID: {user_id}")
        return UserResponse(**user)
    except Exception as e:
        logger.error(f"Error checking user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "DATABASE_ERROR"}
        )

@router.post("/", response_model=UserResponse, status_code=201, tags=["users"], summary="Create User", description="Create a new user using Firebase auth data.")
async def create_user(
    user: UserCreate = Body(..., example={"user_id": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2", "email": "cursordemo249@gmail.com", "display_name": "", "created_at": "2025-06-21T08:00:29.129451", "firebase_uid": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2", "profile_source": "firebase_auth", "is_active": True, "metadata": {"additional_info": "any custom data"}}),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Create a new user using Firebase auth data.
    
    Args:
        user (UserCreate): User data from Firebase auth
        user_repo: User repository instance
        
    Returns:
        UserResponse: Created user details
    """
    logger.info(f"Creating user with Firebase UID: {user.firebase_uid}, email: {user.email}")
    try:
        # Set default display name if empty
        display_name = user.display_name or user.email.split('@')[0]
        
        # Create user with provided Firebase data
        result = await user_repo.create_user(
            email=user.email,
            display_name=display_name,
            user_id=user.user_id,
            firebase_uid=user.firebase_uid,
            profile_source=user.profile_source,
            is_active=user.is_active,
            created_at=user.created_at,
            metadata=user.metadata
        )
        if not result:
            logger.error("Failed to create user: No result returned from database")
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
                headers={"error_code": "DATABASE_ERROR"}
            )
        
        logger.info(f"User created successfully with Firebase UID: {user.firebase_uid}")
        user_response = UserResponse(
            user_id=result["user_id"],
            email=result["email"],
            display_name=result["display_name"],
            created_at=result["created_at"],
            firebase_uid=result["firebase_uid"],
            profile_source=result["profile_source"],
            is_active=result["is_active"],
            updated_at=result["updated_at"],
            cover_image_url=result.get("cover_image_url"),
            metadata=result.get("metadata")
        )
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user with Firebase data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "DATABASE_ERROR"}
        )

@router.get("/{user_id}/stories", response_model=List[Dict[str, Any]], tags=["users"], summary="Get User Stories", description="Get all stories for a user.")
async def get_user_stories(
    user_id: str,
    service: StoryService = Depends(get_story_service)
):
    """Get all stories for a user.
    
    Args:
        user_id: Firebase user ID
        service: StoryService instance
        
    Returns:
        List[Dict[str, Any]]: List of user's stories
        
    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if database error occurs
    """
    logger.info(f"Getting stories for user: {user_id}")
    try:
        stories = await service.get_user_stories(user_id)
        logger.info(f"Successfully retrieved {len(stories)} stories for user: {user_id}")
        return stories
    except Exception as e:
        logger.error(f"Error getting stories for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "DATABASE_ERROR"}
        )

@router.delete("/delete-account", tags=["users"], summary="Delete User Account", description="Delete user account and all associated data.")
async def delete_account(
    user_id: str,
    email: str,
    service: UserService = Depends(get_user_service)
):
    """
    Delete user account and all associated data.
    
    Args:
        user_id: Firebase UID of the user to delete
        email: Email address to validate ownership
    
    Returns:
        dict: Success message or error details
    """
    try:
        result = await service.delete_account(user_id, email)
        return result
    except ValueError as ve:
        logger.error(f"Validation error during account deletion for {user_id}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error deleting account for {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class UserUpdateModel(UserCreate):
    """Model for updating a user (all fields optional except user_id)"""
    email: Optional[str] = None
    username: Optional[str] = None

@router.patch("/{user_id}", response_model=UserResponse, tags=["users"], summary="Update User", description="Update a user's information.")
async def update_user(
    user_id: str,
    user_data: UserUpdateModel = Body(..., example={"email": "new@example.com", "username": "newname"}),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Update a user's information.
    
    Args:
        user_id: Firebase user ID
        user_data: User data to update
        user_repo: User repository instance
        
    Returns:
        UserResponse: Updated user details
    """
    logger.info(f"Updating user with ID: {user_id}")
    try:
        # Filter out None values
        update_data = {k: v for k, v in user_data.dict().items() if v is not None and k != "user_id"}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        result = await user_repo.update_user(user_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User updated successfully: {user_id}")
        return UserResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))