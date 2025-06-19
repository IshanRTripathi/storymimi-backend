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

logger = logging.getLogger(__name__)

class UserRepository(SupabaseBaseClient):
    """Repository for user-related operations"""
    
    async def create_user(self, email: str, username: str) -> Dict[str, Any]:
        """Create a new user in the database with retry logic
        
        Args:
            email: The user's email address
            username: The user's username
            
        Returns:
            The created user data or None if creation failed
            
        Raises:
            APIError: If the API returns an error
            AuthenticationError: If authentication fails
            ConflictError: If the user already exists
            Exception: For other failures
        """
        start_time = time.time()
        user_id = str(uuid.uuid4())
        user_data = {
            "email": email,
            "username": username,
            "user_id": user_id
        }
        
        self._log_operation("insert", "users", user_data)
        logger.info(f"Creating new user with email: {email}, username: {username}, user_id: {user_id}")
        
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay
        
        for attempt in range(max_retries):
            try:
                response = await self.client.table("users").insert(user_data).execute()
                
                if not response.data:
                    logger.error(f"Failed to create user: No data returned from database")
                    return None
                    
                elapsed = time.time() - start_time
                logger.info(f"User created successfully in {elapsed:.2f}s: {user_id}")
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
    
    async def delete_user(self, user_id: Union[str, UUID]) -> bool:
        """Delete a user from the database
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If user deletion fails
        """
        start_time = time.time()
        user_id_str = str(user_id)
        
        self._log_operation("delete", "users", filters={"user_id": user_id_str})
        logger.info(f"Deleting user with ID: {user_id_str}")
        
        try:
            response = self.client.table("users").delete().eq("user_id", user_id_str).execute()
            success = bool(response.data)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"User deleted successfully in {elapsed:.2f}s: {user_id_str}")
            else:
                logger.warning(f"User deletion returned no data in {elapsed:.2f}s: {user_id_str}")
                
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete user in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
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
