from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from app.utils.prompt_limits import get_component_limit


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
    scene_id: UUID = Field(info={"description": "Unique identifier for the scene"})
    story_id: UUID = Field(info={"description": "ID of the story this scene belongs to"})
    sequence: int = Field(info={"description": "Sequence number of the scene in the story"})
    title: str = Field(min_length=1, max_length=200, info={"description": "Scene title"})
    text: str = Field(min_length=1, max_length=5000, info={"description": "Scene text"})
    image_prompt: str = Field(min_length=1, max_length=3000, info={"description": "Prompt for generating scene image"})
    image_url: Optional[str] = Field(
        default=None,
        pattern=r'^https?://[\w.-]+(?:/[\w.-]*)*\??$',
        max_length=2000,
        info={"description": "URL of the scene image"}
    )
    audio_url: Optional[str] = Field(
        default=None,
        pattern=r'^https?://[\w.-]+(?:/[\w.-]*)*\??$',
        max_length=2000,
        info={"description": "URL of the scene audio"}
    )
    created_at: datetime = Field(info={"description": "Creation timestamp"})
    updated_at: datetime = Field(info={"description": "Last update timestamp"})


class StoryRequest(BaseModel):
    """Request model for creating a story"""
    title: str = Field(info={"description": "Title for the story"})
    prompt: str = Field(info={"description": "Prompt for story generation"})
    user_id: UUID = Field(info={"description": "User ID"})


class StoryResponse(BaseModel):
    """Response model for story operations"""
    status: str = Field(info={"description": "Current status of the story"})
    title: str = Field(info={"description": "Title of the story"})
    error: Optional[str] = Field(default=None, info={"description": "Error message if present"})
    story_id: Optional[UUID] = Field(default=None, info={"description": "Story ID"})
    user_id: UUID = Field(info={"description": "User ID"})
    created_at: Optional[datetime] = Field(default=None, info={"description": "Creation timestamp"})
    updated_at: Optional[datetime] = Field(default=None, info={"description": "Last update timestamp"})


class StoryData(BaseModel):
    """Model for AI-generated story content"""
    title: str = Field(info={"description": "Title of the story"})
    scenes: List[Scene] = Field(info={"description": "List of story scenes"})


class StoryDetail(BaseModel):
    """Model for complete story details"""
    story_id: UUID = Field(info={"description": "Story ID"})
    title: str = Field(info={"description": "Title of the story"})
    status: StoryStatus = Field(info={"description": "Current status of the story"})
    scenes: List[Scene] = Field(info={"description": "List of story scenes"})
    user_id: UUID = Field(info={"description": "User ID"})
    created_at: datetime = Field(info={"description": "Creation timestamp"})
    updated_at: datetime = Field(info={"description": "Last update timestamp"})
    story_metadata: Optional[Dict[str, Any]] = Field(default=None, info={"description": "LLM-generated structured story metadata"})


class SceneImagePrompt(BaseModel):
    """Schema for scene image prompt components."""
    style: str = Field(max_length=get_component_limit('base_style'))
    setting: str = Field(max_length=get_component_limit('scene'))
    action: str = Field(max_length=get_component_limit('scene'))
    characters: str = Field(max_length=get_component_limit('characters'))
    time_of_day: Optional[str] = Field(default=None, max_length=get_component_limit('atmosphere'))
    weather: Optional[str] = Field(default=None, max_length=get_component_limit('atmosphere'))
    mood: Optional[str] = Field(default=None, max_length=get_component_limit('atmosphere'))
    technical_details: Optional[str] = Field(default=None, max_length=get_component_limit('technical'))

    @field_validator('*')
    def check_component_length(cls, v, info):
        """Validate that each component stays within its allocated length."""
        max_len = info.field_info.max_length
        if v and max_len and len(v) > max_len:
            raise ValueError(f"{info.name} exceeds maximum length of {max_len} characters")
        return v
