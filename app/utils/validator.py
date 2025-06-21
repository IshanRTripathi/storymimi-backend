from typing import Dict, Any, List, Optional
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
    def validate_email(email: str, is_firebase_auth: bool = True) -> None:
        """Validate email format - simplified for Firebase auth users
        
        Args:
            email: Email address to validate
            is_firebase_auth: If True, use minimal validation (Firebase already validates)
            
        Raises:
            ValueError: If email format is invalid
        """
        if not email:
            raise ValueError("Email cannot be empty")
            
        # For Firebase auth users, minimal validation since Firebase already validates
        if is_firebase_auth:
            # Firebase ensures valid email format, just check it's not empty
            if not email.strip():
                raise ValueError("Email cannot be empty")
            return
            
    @staticmethod
    def validate_model_data(data: Dict[str, Any], is_initial_creation: bool = False, is_completion: bool = False, is_response: bool = False) -> None:
        """Validate database model data - simplified for Firebase auth
        
        Args:
            data: Dictionary containing model data
            is_initial_creation: If True, allows partial data for story creation
            is_completion: If True, allows completion-specific validation
            is_response: If True, allows response-specific validation
            
        Raises:
            ValueError: If validation fails
        """
        logger.info(f"[VALIDATOR] Starting model data validation. is_initial_creation={is_initial_creation}, is_completion={is_completion}")
        logger.debug(f"[VALIDATOR] Data to validate: {data}")
        
        # Skip validation for response models
        if is_response:
            return
        
        # Validate email if present - minimal validation for Firebase users
        if "email" in data:
            try:
                Validator.validate_email(data["email"], is_firebase_auth=True)
            except ValueError as e:
                logger.error(f"[VALIDATOR] Email validation failed: {str(e)}")
                raise ValueError(f"Invalid email: {str(e)}")
        
        # For initial story creation, only require basic fields
        required_fields = ["story_id", "title", "status"]
        
        if not is_initial_creation:
            # For completion validation, scenes are optional in error cases
            if data.get("status") != "failed":
                required_fields.extend(["scenes"])
            
            required_fields.extend(["story_metadata"])
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
        
        # Basic type validation
        if "story_id" in data and not isinstance(data["story_id"], str):
            raise ValueError("Story ID must be a string")
            
        # Simplified user_id validation - Firebase UIDs are already validated
        if "user_id" in data and not isinstance(data["user_id"], str):
            raise ValueError("User ID must be a string")
            
        # Validate timestamps
        if not is_initial_creation:
            if "created_at" not in data or "updated_at" not in data:
                raise ValueError("Timestamps are required for non-initial creation")
            
            # Convert timestamps to ISO format if needed
            try:
                if isinstance(data["created_at"], datetime):
                    data["created_at"] = data["created_at"].isoformat()
                if isinstance(data["updated_at"], datetime):
                    data["updated_at"] = data["updated_at"].isoformat()
            except Exception as e:
                raise ValueError(f"Failed to convert timestamp to ISO format: {str(e)}")
        
        # Validate status
        if "status" in data:
            if not isinstance(data["status"], str):
                raise ValueError("Status must be a string")
            valid_statuses = [StoryStatus.PENDING, StoryStatus.PROCESSING, StoryStatus.COMPLETED, StoryStatus.FAILED]
            if data["status"] not in valid_statuses:
                raise ValueError(f"Invalid status value: {data['status']}. Valid statuses are: {', '.join(valid_statuses)}")
        
        # Validate title
        if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
            raise ValueError("Title must be a non-empty string")
        
        # Validate story_metadata if present and not initial creation
        if not is_initial_creation and "story_metadata" in data:
            if not isinstance(data["story_metadata"], dict):
                raise ValueError("Story metadata must be a dictionary.")
        
        # Validate scenes if present
        if "scenes" in data:
            scenes = data["scenes"]
            if not isinstance(scenes, list):
                raise ValueError("Scenes must be a list")
            logger.info(f"[VALIDATOR] Validating {len(scenes)} scenes")    
            for scene in scenes:
                # Check if scene is already a Scene model instance
                if isinstance(scene, Scene):
                    scene_dict = scene.dict()
                else:
                    if not isinstance(scene, dict):
                        raise ValueError("Each scene must be a dictionary")
                    scene_dict = scene
                
                # Basic scene validation
                required_scene_fields = ["scene_id", "story_id", "sequence", "title", "text"]
                missing_scene_fields = [field for field in required_scene_fields if field not in scene_dict]
                if missing_scene_fields:
                    raise ValueError(f"Scene is missing required fields: {', '.join(missing_scene_fields)}")
                
                # Basic type validation
                if not isinstance(scene_dict["text"], str) or not scene_dict["text"].strip():
                    raise ValueError("Scene text must be a non-empty string")
                if not isinstance(scene_dict["title"], str) or not scene_dict["title"].strip():
                    raise ValueError("Scene title must be a non-empty string")
                if not isinstance(scene_dict["sequence"], int):
                    raise ValueError("Scene sequence must be an integer")

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
