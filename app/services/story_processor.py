import logging
from datetime import datetime
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class StoryProcessor:
    """Service for processing AI-generated story data and adding backend fields"""
    
    def __init__(self):
        """Initialize the processor with timezone settings"""
        self.timezone = settings.TIMEZONE
    
    def add_backend_fields(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add backend-managed fields to story data
        
        Args:
            story_data: AI-generated story data
            
        Returns:
            Story data with backend fields added
        """
        now = datetime.now().isoformat()
        
        # Add story-level backend fields
        story_data["created_at"] = now.isoformat()
        story_data["updated_at"] = now.isoformat()
        story_data["updated_by"] = "system"
        
        # Add scene-level backend fields
        for i, scene in enumerate(story_data.get("scenes", [])):
            scene["created_at"] = now.isoformat()
            scene["updated_at"] = now.isoformat()
            scene["updated_by"] = "system"
            scene["story_id"] = story_data["story_id"]  # Link scene to story
            scene["sequence"] = i + 1  # 1-based sequence
        
        return story_data
