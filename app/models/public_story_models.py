from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID

class AgeRating(str, Enum):
    """Enum for age ratings"""
    ALL = "ALL"
    AGES_3_PLUS = "3+"
    AGES_6_PLUS = "6+"
    AGES_9_PLUS = "9+"
    AGES_12_PLUS = "12+"

class DifficultyLevel(str, Enum):
    """Enum for story difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class StoryCategory(str, Enum):
    """Enum for story categories"""
    FANTASY = "fantasy"
    SCIENCE_FICTION = "science-fiction"
    ADVENTURE = "adventure"
    FRIENDSHIP = "friendship"
    ANIMALS = "animals"
    MYSTERY = "mystery"
    EDUCATIONAL = "educational"

class PublicStoryScene(BaseModel):
    """Model for a public story scene"""
    sequence: int = Field(..., description="Scene order number")
    text: str = Field(..., description="Scene narrative text")
    image_url: Optional[str] = Field(None, description="Scene image URL")
    audio_url: Optional[str] = Field(None, description="Scene audio URL")

class PublicStorySummary(BaseModel):
    """Summary model for story lists and cards"""
    id: UUID = Field(..., description="Story unique identifier")
    title: str = Field(..., description="Story title")
    description: Optional[str] = Field(None, description="Short story description")
    cover_image_url: Optional[str] = Field(None, description="Story cover image URL")
    tags: List[str] = Field(default_factory=list, description="Story tags")
    duration: str = Field(..., description="Estimated reading/listening time")
    featured: bool = Field(False, description="Whether story is featured")
    view_count: int = Field(0, description="Number of views")
    age_rating: AgeRating = Field(AgeRating.ALL, description="Age appropriateness")
    category: StoryCategory = Field(..., description="Story category")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Reading difficulty")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class PublicStoryDetail(PublicStorySummary):
    """Complete story model with scenes"""
    scenes: List[PublicStoryScene] = Field(..., description="Story scenes")
    published: bool = Field(True, description="Whether story is published")

class CategorizedPublicStories(BaseModel):
    """Model for categorized stories"""
    categories: List[str] = Field(..., description="List of available categories")
    stories: Dict[str, List[PublicStorySummary]] = Field(..., description="Stories grouped by category")
