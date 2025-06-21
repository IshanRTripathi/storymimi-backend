from fastapi import APIRouter, HTTPException, Depends, Body, Query
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
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get all stories for a user.
    
    Args:
        user_id: Firebase user ID
        user_repo: User repository instance
        
    Returns:
        List[Dict[str, Any]]: List of user's stories
        
    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if database error occurs
    """
    logger.info(f"Getting stories for user: {user_id}")
    try:
        # First check if user exists
        user = await user_repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"error_code": "USER_NOT_FOUND"}
            )
        
        # Get stories for the user using the stories table
        from app.database.supabase_client.stories_client import StoryRepository
        story_repo = StoryRepository()
        stories = await story_repo.get_stories_by_user_id(user_id)
        
        logger.info(f"Successfully retrieved {len(stories)} stories for user: {user_id}")
        return stories
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stories for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "DATABASE_ERROR"}
        )

@router.get("/{user_id}/creations", response_model=Dict[str, Any], tags=["users"], summary="Get User Creations", description="Get user's stories optimized for Flutter My Creations tab with pagination and enhanced metadata.")
async def get_user_creations(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Number of stories per page"),
    status_filter: Optional[str] = Query(None, description="Filter by story status (pending, processing, completed, failed)"),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get user's stories optimized for Flutter My Creations tab.
    
    Args:
        user_id: Firebase user ID
        page: Page number for pagination
        limit: Number of stories per page
        status_filter: Optional status filter
        user_repo: User repository instance
        
    Returns:
        Dict containing paginated stories with metadata
        
    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if database error occurs
    """
    logger.info(f"Getting creations for user: {user_id}, page: {page}, limit: {limit}, status_filter: {status_filter}")
    try:
        # First check if user exists
        user = await user_repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"error_code": "USER_NOT_FOUND"}
            )
        
        # Get stories for the user using the stories table
        from app.database.supabase_client.stories_client import StoryRepository
        story_repo = StoryRepository()
        
        # Get all stories first (we'll implement pagination in the repository later)
        all_stories = await story_repo.get_stories_by_user_id(user_id)
        
        # Apply status filter if provided
        if status_filter:
            all_stories = [story for story in all_stories if story.get("status") == status_filter]
        
        # Calculate pagination
        total_stories = len(all_stories)
        total_pages = (total_stories + limit - 1) // limit
        start_index = (page - 1) * limit
        end_index = start_index + limit
        
        # Get paginated stories
        paginated_stories = all_stories[start_index:end_index]
        
        # Enhance stories with additional metadata for Flutter
        enhanced_stories = []
        for story in paginated_stories:
            enhanced_story = {
                "story_id": story["story_id"],
                "title": story["title"],
                "status": story["status"],
                "created_at": story["created_at"],
                "updated_at": story.get("updated_at"),
                "cover_image_url": story.get("cover_image_url"),
                "user_id": story["user_id"],
                # Add Flutter-specific fields
                "is_completed": story["status"] == "completed",
                "is_processing": story["status"] == "processing",
                "is_failed": story["status"] == "failed",
                "can_view": story["status"] in ["completed", "failed"],
                "can_retry": story["status"] == "failed",
                "estimated_completion_time": story.get("estimated_completion_time"),
                "progress_percentage": _calculate_progress_percentage(story["status"]),
                "scene_count": story.get("scene_count", 0),
                "duration_minutes": story.get("duration_minutes", 0),
                "tags": story.get("tags", []),
                "category": story.get("category", "general"),
                "age_rating": story.get("age_rating", "all"),
                "difficulty_level": story.get("difficulty_level", "beginner")
            }
            enhanced_stories.append(enhanced_story)
        
        # Prepare response with pagination metadata
        response = {
            "stories": enhanced_stories,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_stories": total_stories,
                "stories_per_page": limit,
                "has_next_page": page < total_pages,
                "has_previous_page": page > 1
            },
            "user_info": {
                "user_id": user["user_id"],
                "display_name": user.get("display_name"),
                "email": user.get("email"),
                "total_creations": total_stories,
                "completed_stories": len([s for s in all_stories if s["status"] == "completed"]),
                "processing_stories": len([s for s in all_stories if s["status"] == "processing"])
            },
            "filters": {
                "applied_status_filter": status_filter,
                "available_statuses": ["pending", "processing", "completed", "failed"]
            }
        }
        
        logger.info(f"Successfully retrieved {len(enhanced_stories)} stories for user: {user_id} (page {page}/{total_pages})")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting creations for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "DATABASE_ERROR"}
        )

def _calculate_progress_percentage(status: str) -> int:
    """Calculate progress percentage based on story status"""
    status_progress = {
        "pending": 0,
        "processing": 50,
        "completed": 100,
        "failed": 0
    }
    return status_progress.get(status, 0)

@router.get("/{user_id}/creations/stats", response_model=Dict[str, Any], tags=["users"], summary="Get User Creation Statistics", description="Get statistics about user's story creations for My Creations tab.")
async def get_user_creation_stats(
    user_id: str,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Get statistics about user's story creations.
    
    Args:
        user_id: Firebase user ID
        user_repo: User repository instance
        
    Returns:
        Dict containing user creation statistics
        
    Raises:
        HTTPException: 404 if user not found
        HTTPException: 500 if database error occurs
    """
    logger.info(f"Getting creation statistics for user: {user_id}")
    try:
        # First check if user exists
        user = await user_repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"error_code": "USER_NOT_FOUND"}
            )
        
        # Get stories for the user
        from app.database.supabase_client.stories_client import StoryRepository
        story_repo = StoryRepository()
        all_stories = await story_repo.get_stories_by_user_id(user_id)
        
        # Calculate statistics
        total_stories = len(all_stories)
        completed_stories = len([s for s in all_stories if s["status"] == "completed"])
        processing_stories = len([s for s in all_stories if s["status"] == "processing"])
        pending_stories = len([s for s in all_stories if s["status"] == "pending"])
        failed_stories = len([s for s in all_stories if s["status"] == "failed"])
        
        # Calculate success rate
        success_rate = (completed_stories / total_stories * 100) if total_stories > 0 else 0
        
        # Get recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_stories = [
            s for s in all_stories 
            if datetime.fromisoformat(s["created_at"].replace('Z', '+00:00')) > thirty_days_ago
        ]
        
        # Calculate average creation time (for completed stories)
        completed_story_times = []
        for story in all_stories:
            if story["status"] == "completed" and story.get("created_at") and story.get("updated_at"):
                try:
                    created = datetime.fromisoformat(story["created_at"].replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(story["updated_at"].replace('Z', '+00:00'))
                    creation_time = (updated - created).total_seconds() / 60  # in minutes
                    completed_story_times.append(creation_time)
                except:
                    continue
        
        avg_creation_time = sum(completed_story_times) / len(completed_story_times) if completed_story_times else 0
        
        # Prepare response
        stats = {
            "user_info": {
                "user_id": user["user_id"],
                "display_name": user.get("display_name"),
                "email": user.get("email")
            },
            "overview": {
                "total_creations": total_stories,
                "completed_stories": completed_stories,
                "processing_stories": processing_stories,
                "pending_stories": pending_stories,
                "failed_stories": failed_stories,
                "success_rate": round(success_rate, 1)
            },
            "activity": {
                "recent_creations": len(recent_stories),
                "avg_creation_time_minutes": round(avg_creation_time, 1),
                "last_creation_date": all_stories[0]["created_at"] if all_stories else None,
                "most_active_day": _get_most_active_day(all_stories)
            },
            "performance": {
                "completion_rate": round((completed_stories / total_stories * 100), 1) if total_stories > 0 else 0,
                "failure_rate": round((failed_stories / total_stories * 100), 1) if total_stories > 0 else 0,
                "avg_stories_per_month": round(total_stories / max(1, _calculate_months_since_first_story(all_stories)), 1)
            }
        }
        
        logger.info(f"Successfully retrieved creation statistics for user: {user_id}")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting creation statistics for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
            headers={"error_code": "DATABASE_ERROR"}
        )

def _get_most_active_day(stories: List[Dict[str, Any]]) -> Optional[str]:
    """Get the day when user created the most stories"""
    if not stories:
        return None
    
    from collections import Counter
    from datetime import datetime
    
    creation_dates = []
    for story in stories:
        try:
            created = datetime.fromisoformat(story["created_at"].replace('Z', '+00:00'))
            creation_dates.append(created.strftime('%Y-%m-%d'))
        except:
            continue
    
    if not creation_dates:
        return None
    
    date_counts = Counter(creation_dates)
    most_active_date = date_counts.most_common(1)[0][0]
    return most_active_date

def _calculate_months_since_first_story(stories: List[Dict[str, Any]]) -> int:
    """Calculate months since the first story was created"""
    if not stories:
        return 1
    
    from datetime import datetime
    
    try:
        first_story_date = datetime.fromisoformat(stories[-1]["created_at"].replace('Z', '+00:00'))
        current_date = datetime.now()
        months_diff = (current_date.year - first_story_date.year) * 12 + (current_date.month - first_story_date.month)
        return max(1, months_diff)
    except:
        return 1

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