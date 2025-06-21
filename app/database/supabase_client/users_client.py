from typing import Dict, Optional, Any, Union, List
from uuid import UUID
from datetime import datetime
from asyncio import sleep
from app.database.supabase_client.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    GatewayTimeoutError,
    InternalServerError,
    NotFoundError,
    ServiceUnavailableError,
    TimeoutError,
    TooManyRequestsError,
    UnauthorizedError,
    RetryableError,
    NonRetryableError,
    ValidationError
)
import logging
import time
import uuid

from app.database.supabase_client.base_client import SupabaseBaseClient
from app.models.user import User, UserResponse
from app.utils.validator import Validator

logger = logging.getLogger(__name__)

class UserRepository(SupabaseBaseClient):
    """Repository for user-related operations"""
    
    def __init__(self):
        """Initialize the repository with a Supabase client instance"""
        super().__init__()
        logger.info("UserRepository initialized successfully")
    
    async def create_user(self, email: str, display_name: Optional[str], user_id: str, firebase_uid: str, profile_source: str, is_active: bool, created_at: datetime, metadata: Optional[dict] = None) -> Dict[str, Any]:
        """Create a new user in the database with retry logic
        
        Args:
            email: The user's email address
            display_name: The user's display name (optional)
            user_id: The Firebase user ID
            firebase_uid: The Firebase UID
            profile_source: Source of the profile (firebase_auth/manual/other)
            is_active: User's active status
            created_at: User creation timestamp
            metadata: Custom metadata (optional)
            
        Returns:
            The created user data or None if creation failed
            
        Raises:
            APIError: If the API returns an error
            AuthenticationError: If authentication fails
            ConflictError: If the user already exists
            Exception: For other failures
        """
        start_time = time.time()
        user_data = {
            "email": email.lower(),  # Normalize email to lowercase
            "display_name": display_name,
            "user_id": user_id,
            "firebase_uid": firebase_uid,
            "profile_source": profile_source,
            "is_active": is_active,
            "created_at": created_at.isoformat(),
            "metadata": metadata or {}
        }
        
        self._log_operation("insert", "users", user_data)
        logger.info(f"Creating new user with email: {email}, display_name: {display_name}, user_id: {user_id}")
        
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                response = self.client.table("users").insert(user_data).execute()
                
                if not response.data:
                    logger.error(f"Failed to create user with email {email}: No data returned from database")
                    return None
                    
                elapsed = time.time() - start_time
                logger.info(f"User created successfully in {elapsed:.2f}s: user_id={user_id}, email={email}")
                return response.data[0]
                
            except ConflictError as e:
                logger.error(f"User creation conflict: {str(e)}")
                raise
                
            except (APIError, AuthenticationError, InternalServerError, ServiceUnavailableError, RetryableError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to create user after {max_retries} attempts: {str(e)}", exc_info=True)
                    raise
                    
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}, retrying in {retry_delay} seconds")
                await sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
            except (BadRequestError, ForbiddenError, UnauthorizedError, NonRetryableError) as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed to create user in {elapsed:.2f}s: {str(e)}", exc_info=True)
                raise
    
    async def get_user(self, user_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a user by ID
        
        Args:
            user_id: The ID of the user to retrieve
            
        Returns:
            The user data or None if not found
            
        Raises:
            Exception: If user retrieval fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("select", "users", filters={"user_id": user_id_str})
        logger.info(f"Getting user with ID: {user_id_str}")
        
        try:
            response = self.client.table("users").select("*").eq("user_id", user_id_str).execute()
            
            if not response.data:
                logger.warning(f"User not found with ID: {user_id_str}")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"User retrieved successfully in {elapsed:.2f}s: {user_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get user in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def update_user(self, user_id: Union[str, UUID], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's information
        
        Args:
            user_id: The ID of the user to update
            data: Dictionary containing fields to update
            
        Returns:
            The updated user data or None if update failed
            
        Raises:
            Exception: If user update fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("update", "users", data, filters={"user_id": user_id_str})
        logger.info(f"Updating user with ID: {user_id_str}, fields: {list(data.keys())}")
        
        try:
            response = self.client.table("users").update(data).eq("user_id", user_id_str).execute()
            
            if not response.data:
                logger.warning(f"User update failed, no data returned: {user_id_str}")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"User updated successfully in {elapsed:.2f}s: {user_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update user in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user from the database with retry logic
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if the user was successfully deleted, False otherwise
            
        Raises:
            APIError: If the API returns an error
        """
        try:
            logger.info(f"Attempting to delete user with ID: {user_id}")
            result = self.client.table("users").delete().eq("user_id", str(user_id)).execute()
            logger.info(f"Delete result: {result}")
            return bool(result.data)
                
        except Exception as e:
            logger.error(f"Error deleting user with ID {user_id}: {str(e)}", exc_info=True)
            raise APIError(f"Error deleting user: {str(e)}")

    async def update_user_cover_image(self, user_id: Union[str, UUID], cover_image_url: str) -> bool:
        """Update a user's cover image URL
        
        Args:
            user_id: The ID of the user to update
            cover_image_url: The URL of the cover image
            
        Returns:
            True if the cover image was successfully updated, False otherwise
            
        Raises:
            Exception: If cover image update fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("update", "users", {"cover_image_url": cover_image_url}, filters={"user_id": user_id_str})
        logger.info(f"Updating cover image for user: {user_id_str}")
        
        try:
            response = self.client.table("users").update({"cover_image_url": cover_image_url}).eq("user_id", user_id_str).execute()
            
            if not response.data:
                logger.warning(f"Cover image update failed, no data returned: {user_id_str}")
                return False
                
            elapsed = time.time() - start_time
            logger.info(f"Cover image updated successfully in {elapsed:.2f}s for user: {user_id_str}")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to update cover image in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise

    async def get_user_stories(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all stories associated with a user
        
        Args:
            user_id: The ID of the user to get stories for
            
        Returns:
            List of story dictionaries associated with the user
            
        Raises:
            NotFoundError: If no stories are found for the user
            APIError: If there's an error fetching the stories
        """
        try:
            logger.info(f"Fetching stories for user ID: {user_id}")
            result = self.client.table("stories").select("*").eq("user_id", str(user_id)).execute()
            
            if not result.data:
                raise NotFoundError(f"No stories found for user ID: {user_id}")
            
            logger.info(f"Found {len(result.data)} stories for user ID: {user_id}")
            return result.data
            
        except NotFoundError as e:
            logger.warning(f"No stories found for user ID {user_id}: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Error fetching stories for user ID {user_id}: {str(e)}", exc_info=True)
            raise APIError(f"Error fetching stories: {str(e)}")

    async def get_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get a list of users with pagination
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user data dictionaries
            
        Raises:
            Exception: If user retrieval fails
        """
        start_time = time.time()
        
        self._log_operation("select", "users", filters={"limit": limit, "offset": offset})
        logger.info(f"Getting users with limit: {limit}, offset: {offset}")
        
        try:
            response = self.client.table("users").select("*").range(offset, offset + limit - 1).execute()
            users = response.data if response.data else []
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(users)} users successfully in {elapsed:.2f}s")
            return users
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get users in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
