from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime

class User(BaseModel):
    """User model"""
    user_id: UUID = Field(default_factory=uuid4, description="Unique identifier for the user")
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")
    cover_image_url: Optional[str] = Field(None, description="URL of the user's cover image (from first story scene)")
    created_at: datetime = Field(default_factory=datetime.now, description="When the user was created")
    updated_at: Optional[datetime] = Field(None, description="When the user was last updated")

class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")

class UserUpdate(BaseModel):
    """Model for updating a user"""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    username: Optional[str] = Field(None, description="User's username")
    cover_image_url: Optional[str] = Field(None, description="URL of the user's cover image")

class UserResponse(BaseModel):
    """Response model for user data"""
    user_id: UUID = Field(..., description="Unique identifier for the user")
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")
    cover_image_url: Optional[str] = Field(None, description="URL of the user's cover image")
    created_at: datetime = Field(..., description="When the user was created")

class UserStoriesResponse(BaseModel):
    """Response model for a user's stories"""
    user_id: UUID = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="User's username")
    story_ids: List[UUID] = Field(default_factory=list, description="List of story IDs created by the user")