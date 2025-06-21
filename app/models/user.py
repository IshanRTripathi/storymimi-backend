from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

class User(BaseModel):
    """User model"""
    user_id: str = Field(..., description="Firebase user ID")
    email: EmailStr = Field(..., description="User's email address")
    display_name: Optional[str] = Field(None, description="User's display name")
    created_at: datetime = Field(..., description="When the user was created")
    firebase_uid: str = Field(..., description="Firebase UID")
    profile_source: str = Field(..., description="Source of profile (e.g., firebase_auth)")
    is_active: bool = Field(..., description="User's active status")
    updated_at: Optional[datetime] = Field(None, description="When the user was last updated")
    cover_image_url: Optional[str] = Field(None, description="URL of the user's cover image")
    metadata: Optional[dict] = Field(None, description="Custom metadata JSON")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
                "email": "cursordemo249@gmail.com",
                "display_name": "",
                "created_at": "2025-06-21T08:00:29.129451",
                "firebase_uid": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
                "profile_source": "firebase_auth",
                "is_active": True,
                "updated_at": "2025-06-21T08:00:29.129451",
                "cover_image_url": "https://example.com/image.jpg",
                "metadata": {
                    "additional_info": "any custom data"
                }
            }
        }

class UserCreate(BaseModel):
    """Model for creating a new user with Firebase auth data"""
    user_id: str = Field(..., description="Firebase user ID")
    email: EmailStr = Field(..., description="User's email address")
    display_name: Optional[str] = Field(None, description="User's display name")
    created_at: datetime = Field(..., description="When the user was created")
    firebase_uid: str = Field(..., description="Firebase UID")
    profile_source: str = Field(..., description="Profile source (firebase_auth/manual/other)")
    is_active: bool = Field(default=True, description="User's active status")
    metadata: Optional[dict] = Field(None, description="Custom metadata JSON")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
                "email": "cursordemo249@gmail.com",
                "display_name": "",
                "created_at": "2025-06-21T08:00:29.129451",
                "firebase_uid": "xHyXCebE7pdl8xPJ7g5n1jmS5WP2",
                "profile_source": "firebase_auth",
                "is_active": True,
                "metadata": {
                    "additional_info": "any custom data"
                }
            }
        }



class UserUpdate(BaseModel):
    """Model for updating a user"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    username: Optional[str] = Field(None, description="User's username")
    cover_image_url: Optional[str] = Field(None, description="URL of the user's cover image")

class UserResponse(BaseModel):
    """Response model for user data"""
    user_id: str = Field(..., description="Firebase user ID")
    email: EmailStr = Field(..., description="User's email address")
    display_name: Optional[str] = Field(None, description="User's display name")
    created_at: datetime = Field(..., description="When the user was created")
    firebase_uid: str = Field(..., description="Firebase UID")
    profile_source: str = Field(..., description="Profile source (firebase_auth/manual/other)")
    is_active: bool = Field(..., description="User's active status")
    updated_at: Optional[datetime] = Field(None, description="When the user was last updated")
    cover_image_url: Optional[str] = Field(None, description="URL of the user's cover image")
    metadata: Optional[dict] = Field(None, description="Custom metadata JSON")

class UserStoriesResponse(BaseModel):
    """Response model for a user's stories"""
    user_id: str = Field(..., description="Firebase user ID")
    display_name: Optional[str] = Field(None, description="User's display name")
    story_ids: List[str] = Field(default_factory=list, description="List of story IDs created by the user")