from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from enum import Enum

class StoryStatus(str, Enum):
    """Enum for story status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def validate(cls, value: str) -> bool:
        """Validate if a status value is valid"""
        return value in cls._value2member_map_

class Scene(BaseModel):
    """Model for a story scene"""
    scene_id: UUID = Field(description="Unique identifier for the scene")
    story_id: UUID = Field(description="ID of the story this scene belongs to")
    sequence: int = Field(description="Sequence number of the scene in the story")
    title: str = Field(description="Scene title", min_length=1, max_length=200)
    text: str = Field(description="Scene text", min_length=1, max_length=5000)
    image_prompt: str = Field(description="Prompt for generating scene image", min_length=1, max_length=3000)
    image_url: Optional[str] = Field(
        None,
        description="URL of the scene image",
        pattern=r'^https?://[\w.-]+(?:/[\w.-]*)*\??$',
        max_length=2000
    )
    audio_url: Optional[str] = Field(
        None,
        description="URL of the scene audio",
        pattern=r'^https?://[\w.-]+(?:/[\w.-]*)*\??$',
        max_length=2000
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    

class StoryRequest(BaseModel):
    """Request model for creating a story"""
    title: str = Field(description="Title for the story")
    prompt: str = Field(description="Prompt for story generation")
    user_id: UUID = Field(description="User ID")


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
    scenes: List[Scene] = Field(description="List of story scenes")

class StoryDetail(BaseModel):
    """Model for complete story details"""
    story_id: UUID = Field(description="Story ID")
    title: str = Field(description="Title of the story")
    status: StoryStatus = Field(description="Current status of the story")
    scenes: List[Scene] = Field(description="List of story scenes")
    user_id: UUID = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    story_metadata: Optional[Dict[str, Any]] = Field(None, description="LLM-generated structured story metadata")
