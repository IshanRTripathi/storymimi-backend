from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.story import StoryStatus

@dataclass
class Scene:
    """Represents a single scene in a story"""
    text: str
    image_prompt: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert Scene to dictionary for database storage"""
        return {
            "text": self.text,
            "image_prompt": self.image_prompt,
            "image_url": self.image_url,
            "audio_url": self.audio_url
        }

@dataclass
class Story:
    """Represents a complete story"""
    story_id: str
    title: str
    scenes: List[Scene]
    status: str
    user_id: str
    created_at: str
    updated_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert Story to dictionary for database storage"""
        return {
            "story_id": self.story_id,
            "title": self.title,
            "scenes": [scene.to_dict() for scene in self.scenes],
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

@dataclass
class StoryResponse:
    """Response object for story operations"""
    status: str
    story_id: str
    title: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert StoryResponse to dictionary"""
        return {
            "status": self.status,
            "story_id": self.story_id,
            "title": self.title,
            "error": self.error
        }
