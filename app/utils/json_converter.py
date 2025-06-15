import json
import logging
from typing import Dict, Any, List, Type
from pydantic import BaseModel
from app.models.story_types import Scene, StoryResponse, StoryDetail, StoryStatus
from datetime import datetime
from uuid import UUID
from app.utils.validator import Validator

logger = logging.getLogger(__name__)

class JSONConverter:
    """Utility class for converting between JSON and Python objects"""

    @staticmethod
    def to_scene(data: Dict[str, Any]) -> Scene:
        """Convert AI response data to Scene object
        
        Args:
            data: Dictionary containing scene data
            
        Returns:
            Scene object
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            return Scene(
                scene_id=data["scene_id"],
                title=data["title"],
                text=data["text"],
                image_prompt=data["image_prompt"],
                image_url=data.get("image_url"),
                audio_url=data.get("audio_url"),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating Scene: {str(e)}")

    @staticmethod
    def to_story_response(data: str | Dict[str, Any]) -> StoryResponse:
        """Convert AI response data to StoryResponse object
        
        Args:
            data: Dictionary containing story response data
            
        Returns:
            StoryResponse object
            
        Raises:
            ValueError: If required fields are missing or validation fails
        """
        try:
            if isinstance(data, str):
                # Try to parse as JSON
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as plain text
                    return StoryResponse(
                        status=data["status"],
                        title=data["title"],
                        error=data.get("error")
                    )
            
            return StoryResponse(
                status=data["status"],
                title=data["title"],
                error=data.get("error"),
                user_id=data["user_id"]
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating StoryResponse: {str(e)}")

    @staticmethod
    def from_scene(scene: Scene) -> Dict[str, Any]:
        """Convert Scene object to dictionary containing AI response data"""
        return {
            "scene_id": str(scene.scene_id),
            "title": scene.title,
            "text": scene.text,
            "image_prompt": scene.image_prompt,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "created_at": scene.created_at.isoformat() if scene.created_at else None,
            "updated_at": scene.updated_at.isoformat() if scene.updated_at else None
        }

    @staticmethod
    def from_story_response(response: Any) -> Dict[str, Any]:
        """Convert response to dictionary
        
        Args:
            response: Response object or dictionary
            
        Returns:
            Dictionary representation of the response
        """
        if isinstance(response, dict):
            return {
                "status": response.get("status", "UNKNOWN"),
                "title": response.get("title", ""),
                "error": response.get("error", None),
                "story_id": str(response.get("story_id", None)) if response.get("story_id") else None,
                "user_id": str(response.get("user_id", None)) if response.get("user_id") else None
            }
        return {
            "status": response.status,
            "title": response.title,
            "error": response.error,
            "story_id": str(response.story_id) if response.story_id else None
        }

    @staticmethod
    def from_story_detail(detail: StoryDetail) -> Dict[str, Any]:
        """Convert StoryDetail to dictionary
        
        Args:
            detail: StoryDetail object
            
        Returns:
            Dictionary representation of the detail
        """
        return {
            "story_id": str(detail.story_id),
            "title": detail.title,
            "status": detail.status,
            "scenes": detail.scenes,
            "user_id": str(detail.user_id),
            "created_at": detail.created_at.isoformat(),
            "updated_at": detail.updated_at.isoformat()
        }

    @staticmethod
    def to_story_detail(data: Dict[str, Any]) -> StoryDetail:
        """Convert dictionary to StoryDetail object
        
        Args:
            data: Dictionary containing story detail
            
        Returns:
            StoryDetail object
        
        Raises:
            ValueError: If validation fails
        """
        Validator.validate_model_data(data, is_initial_creation=True)
        return StoryDetail(
            story_id=data["story_id"],
            title=data["title"],
            status=data["status"],
            scenes=data["scenes"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

    @staticmethod
    def parse_json(data: Any, cls: Type[BaseModel]) -> BaseModel:
        """Parse JSON string or dict to object
        
        Args:
            data: JSON string or dictionary
            cls: Class to convert to
            
        Returns:
            Converted object
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            logger.info(f'Received json to convert : {data}')
            if isinstance(data, str):
                json_data = json.loads(data)
            else:
                json_data = data
            
            if cls == Scene:
                return JSONConverter.to_scene(json_data)
            elif cls == StoryResponse:
                return JSONConverter.to_story_response(json_data)
            else:
                raise ValueError(f"Unsupported class: {cls.__name__}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            raise ValueError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error converting JSON to {cls.__name__}: {str(e)}")
            raise ValueError(f"Error converting JSON: {str(e)}")

    @staticmethod
    def to_json(obj: BaseModel) -> str:
        """Convert object to JSON string
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON string
        """
        try:
            if isinstance(obj, Scene):
                data = JSONConverter.from_scene(obj)
            elif isinstance(obj, Story):
                data = JSONConverter.from_story(obj)
            elif isinstance(obj, StoryResponse):
                data = JSONConverter.from_story_response(obj)
            else:
                raise ValueError(f"Unsupported object type: {type(obj).__name__}")
            
            return json.dumps(data)
        except Exception as e:
            logger.error(f"Error converting object to JSON: {str(e)}")
            raise ValueError(f"Error converting to JSON: {str(e)}")
