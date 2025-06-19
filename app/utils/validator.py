from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from app.models.story_types import Scene, StoryStatus
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f"[VALIDATOR] Starting model data validation. is_initial_creation={is_initial_creation}, is_completion={is_completion}")
        logger.debug(f"[VALIDATOR] Data to validate: {data}")
        
        # For initial story creation, only require basic fields
        required_fields = ["story_id", "title", "status"]
        
        if not is_initial_creation:
            # For completion validation, scenes are optional in error cases
            if data.get("status") != "failed":
                required_fields.extend(["scenes"])
            
            # Add story_metadata to required fields for non-initial creation if it's expected
            # Based on the user's input, it's created once and then referred by other flows.
            # So, if not initial creation, it should be present.
            required_fields.extend(["story_metadata"])
            
            # Always require timestamps for non-initial creation
            required_fields.extend(["created_at", "updated_at"])
            
            # Only require user_id if it's not a failed status
            if data.get("status") != "failed":
                required_fields.extend(["user_id"])
            
            # For failed status, add error message if present
            if data.get("status") == "failed" and "error" in data:
                required_fields.extend(["error"])
            
        logger.info(f"[VALIDATOR] Required fields for validation: {required_fields}")
        
        # Check for missing required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"[VALIDATOR] Missing required fields: {missing_fields}")
            logger.error(f"[VALIDATOR] Available fields in data: {list(data.keys())}")
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        logger.info("[VALIDATOR] All required fields present, proceeding with type validation")
        
        # Validate field types
        if not isinstance(data["story_id"], str):
            raise ValueError("Story ID must be a string")
            
        if not isinstance(data["user_id"], (str, UUID)):
            raise ValueError("User ID must be a string or UUID")
            
        # Validate timestamps
        if not is_initial_creation:
            if "created_at" not in data or "updated_at" not in data:
                raise ValueError("Timestamps are required for non-initial creation")
            
            # Validate timestamps are strings
            if not isinstance(data["created_at"], str) or not isinstance(data["updated_at"], str):
                raise ValueError("Timestamps must be strings")
                
            # Validate timestamps are valid ISO format strings
            try:
                datetime.fromisoformat(data["created_at"])
                datetime.fromisoformat(data["updated_at"])
            except ValueError:
                raise ValueError("Timestamps must be valid ISO format strings")
                
            # Validate created_at is not after updated_at
            if data["created_at"] > data["updated_at"]:
                raise ValueError("created_at cannot be after updated_at")
        
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
        
        # Validate story_metadata if present and not initial creation
        if not is_initial_creation and "story_metadata" in data:
            if not isinstance(data["story_metadata"], dict):
                raise ValueError("Story metadata must be a dictionary.")
            # Further detailed validation of story_metadata can be added here if its internal structure is strictly defined.
            # For now, we'll assume the LLM output is mostly trusted or validated at the prompt service level.
        
        # Validate scenes if present
        if "scenes" in data:
            scenes = data["scenes"]
            if not isinstance(scenes, list):
                raise ValueError("Scenes must be a list")
            logger.info(f"[VALIDATOR] Validating {len(scenes)} scenes - {scenes}")    
            for scene in scenes:
                # Check if scene is already a Scene model instance
                if isinstance(scene, Scene):
                    scene_dict = scene.dict()
                else:
                    # If not, ensure it's a dictionary
                    if not isinstance(scene, dict):
                        raise ValueError("Each scene must be a dictionary")
                    scene_dict = scene
                # Validate required scene fields
                required_scene_fields = ["scene_id", "story_id", "sequence", "title", "text", "image_prompt", "image_url", "audio_url", "created_at", "updated_at"]
                missing_scene_fields = [field for field in required_scene_fields if field not in scene_dict]
                if missing_scene_fields:
                    raise ValueError(f"Scene is missing required fields: {', '.join(missing_scene_fields)}")
                # Validate field types
                if not isinstance(scene_dict["text"], str) or not scene_dict["text"].strip():
                    raise ValueError("Scene text must be a non-empty string")
                if not isinstance(scene_dict["title"], str) or not scene_dict["title"].strip():
                    raise ValueError("Scene title must be a non-empty string")
                if not isinstance(scene_dict["image_prompt"], str) or not scene_dict["image_prompt"].strip():
                    raise ValueError("Scene image_prompt must be a non-empty string")
                if not isinstance(scene_dict["sequence"], int):
                    raise ValueError("Scene sequence must be an integer")
                # image_url and audio_url can be None or str
                if scene_dict["image_url"] is not None and not isinstance(scene_dict["image_url"], str):
                    raise ValueError("Scene image_url must be a string or None")
                if scene_dict["audio_url"] is not None and not isinstance(scene_dict["audio_url"], str):
                    raise ValueError("Scene audio_url must be a string or None")
                

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
