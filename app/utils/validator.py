from typing import Dict, Any, List, Optional
from uuid import UUID
from app.models.story_types import StoryStatus


class Validator:
    """Simple validator for story data structures"""
    
    @staticmethod
    def validate_ai_response(data: Dict[str, Any]) -> None:
        """Validate AI-generated story response
        
        Args:
            data: Dictionary containing AI response
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ["title", "scenes"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(data["title"], str) or not data["title"].strip():
            raise ValueError("Title must be a non-empty string")
        
        scenes = data["scenes"]
        if not isinstance(scenes, list):
            raise ValueError("Scenes must be a list")
            
    @staticmethod
    def validate_model_data(data: Dict[str, Any], is_initial_creation: bool = False, is_completion: bool = False) -> None:
        """Validate database model data
        
        Args:
            data: Dictionary containing model data
            is_initial_creation: If True, allows partial data for story creation
            is_completion: If True, allows completion-specific validation
            
        Raises:
            ValueError: If validation fails
        """
        # For initial story creation, only require basic fields
        required_fields = ["story_id", "title", "status"]
        
        if not is_initial_creation:
            # For completion validation, scenes are optional in error cases
            if data.get("status") != "failed":
                required_fields.extend(["scenes"])
            required_fields.extend(["created_at", "updated_at", "user_id"])
            
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
                
        if not isinstance(data["story_id"], str):
            raise ValueError("Story ID must be a string")
            
        if not isinstance(data["user_id"], (str, UUID)):
            raise ValueError("User ID must be a string or UUID")
            
        if not is_initial_creation:
            if not isinstance(data["created_at"], str) or not isinstance(data["updated_at"], str):
                raise ValueError("Timestamps must be strings")
        
        # Validate status
        if "status" in data:
            if not isinstance(data["status"], str):
                raise ValueError("Status must be a string")
            valid_statuses = [StoryStatus.PENDING, StoryStatus.PROCESSING, StoryStatus.COMPLETED, StoryStatus.FAILED]
            if data["status"] not in valid_statuses:
                raise ValueError(f"Invalid status value: {data['status']}. Valid statuses are: {', '.join(valid_statuses)}")
        
        # Validate title
        if not isinstance(data["title"], str) or not data["title"].strip():
            raise ValueError("Title must be a non-empty string")
        
        # Validate scenes if present
        if "scenes" in data:
            scenes = data["scenes"]
            if not isinstance(scenes, list):
                raise ValueError("Scenes must be a list")
            for scene in scenes:
                if not isinstance(scene, dict):
                    raise ValueError("Each scene must be a dictionary")
                if "text" not in scene:
                    raise ValueError("Each scene must have a 'text' field")
                if not isinstance(scene["text"], str) or not scene["text"].strip():
                    raise ValueError("Scene text must be a non-empty string")

    @staticmethod
    def validate_scene(scene: Dict[str, Any]) -> None:
        """Validate a single scene
        
        Args:
            scene: Dictionary containing scene data
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ["text", "sequence"]
        for field in required_fields:
            if field not in scene:
                raise ValueError(f"Scene missing required field: {field}")
                
        if not isinstance(scene["text"], str) or not scene["text"].strip():
            raise ValueError("Scene text must be a non-empty string")
            
        if not isinstance(scene["sequence"], int):
            raise ValueError("Sequence must be an integer")
