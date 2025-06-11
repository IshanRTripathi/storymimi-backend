from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class StoryStatus(str, Enum):
    """Enum for story generation status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

class StoryRequest(BaseModel):
    """User input for story generation"""
    title: str = Field(..., description="Title of the story")
    prompt: str = Field(..., description="Prompt for story generation")
    style: Optional[str] = Field(None, description="Style of the story (e.g., fantasy, sci-fi)")
    num_scenes: int = Field(3, description="Number of scenes to generate", ge=1, le=10)
    user_id: Optional[UUID] = Field(None, description="ID of the user requesting the story")

class StoryResponse(BaseModel):
    """Initial response with story ID and status"""
    story_id: UUID = Field(..., description="Unique identifier for the story")
    status: StoryStatus = Field(..., description="Current status of story generation")
    created_at: datetime = Field(default_factory=datetime.now, description="When the story was created")

class Scene(BaseModel):
    """Individual scene details"""
    scene_id: UUID = Field(default_factory=uuid4, description="Unique identifier for the scene")
    story_id: UUID = Field(..., description="ID of the story this scene belongs to")
    sequence: int = Field(..., description="Sequence number of the scene in the story", ge=0)
    text: str = Field(..., description="Text content of the scene")
    image_url: Optional[str] = Field(None, description="URL to the scene's image")
    audio_url: Optional[str] = Field(None, description="URL to the scene's audio narration")
    created_at: datetime = Field(default_factory=datetime.now, description="When the scene was created")

class StoryDetail(BaseModel):
    """Full story with scenes"""
    story_id: UUID = Field(..., description="Unique identifier for the story")
    title: str = Field(..., description="Title of the story")
    status: StoryStatus = Field(..., description="Current status of story generation")
    user_id: Optional[UUID] = Field(None, description="ID of the user who created the story")
    created_at: datetime = Field(..., description="When the story was created")
    updated_at: Optional[datetime] = Field(None, description="When the story was last updated")
    scenes: List[Scene] = Field(default_factory=list, description="List of scenes in the story")