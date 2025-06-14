from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class StoryStatus:
    """Class containing story status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def validate(cls, value: str) -> bool:
        """Validate if a status value is valid"""
        return value in cls.__dict__.values()

class Scene(BaseModel):
    """Model for a story scene"""
    scene_id: Optional[UUID] = Field(None, description="Unique identifier for the scene")
    title: str = Field(description="Scene title")
    description: str = Field(description="Scene description")
    text: str = Field(description="Scene text")
    image_prompt: str = Field(description="Prompt for generating scene image")
    image_url: Optional[str] = Field(None, description="URL of the scene image")
    audio_url: Optional[str] = Field(None, description="URL of the scene audio")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class StoryRequest(BaseModel):
    """Request model for creating a story"""
    title: str = Field(description="Title of the story")
    prompt: str = Field(description="Prompt for story generation")
    user_id: UUID = Field(description="User ID")
    style: Optional[str] = Field(None, description="Story style")
    num_scenes: Optional[int] = Field(5, description="Number of scenes")

class StoryResponse(BaseModel):
    """Response model for story operations"""
    status: str = Field(description="Current status of the story")
    title: str = Field(description="Title of the story")
    error: Optional[str] = Field(None, description="Error message if present")
    story_id: Optional[UUID] = Field(None, description="Story ID")
    user_id: UUID = Field(description="User ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class StoryData(BaseModel):
    """Model for AI-generated story content"""
    title: str = Field(description="Title of the story")
    scenes: List[dict] = Field(description="List of story scenes")

class StoryDetail(BaseModel):
    """Model for complete story details"""
    story_id: UUID = Field(description="Story ID")
    title: str = Field(description="Title of the story")
    status: str = Field(description="Current status of the story")
    scenes: List[dict] = Field(description="List of story scenes")
    user_id: UUID = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
