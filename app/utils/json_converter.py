import json
import logging
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel
from app.models.story import Scene, StoryResponse
from datetime import datetime
from uuid import UUID
from app.models.story import StoryStatus

logger = logging.getLogger(__name__)

class JSONConverter:
    """Utility class for converting between JSON and Python objects"""

    @staticmethod
    def to_scene(data: Dict[str, Any]) -> Scene:
        """Convert JSON data to Scene object
        
        Args:
            data: Dictionary containing scene data
            
        Returns:
            Scene object
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            return Scene(
                scene_id=UUID(data["scene_id"]),
                story_id=UUID(data["story_id"]),
                sequence=data["sequence"],
                text=data["text"],
                image_url=data.get("image_url"),
                audio_url=data.get("audio_url"),
                created_at=datetime.fromisoformat(data["created_at"])
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating Scene: {str(e)}")

    @staticmethod
    def to_story_response(data: Dict[str, Any]) -> StoryResponse:
        """Convert JSON data to StoryResponse object
        
        Args:
            data: Dictionary containing story response data
            
        Returns:
            StoryResponse object
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            return StoryResponse(
                story_id=UUID(data["story_id"]),
                status=StoryStatus(data["status"]),
                title=data["title"],
                created_at=datetime.fromisoformat(data["created_at"])
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating StoryResponse: {str(e)}")

    @staticmethod
    def from_scene(scene: Scene) -> Dict[str, Any]:
        """Convert Scene object to JSON data
        
        Args:
            scene: Scene object
            
        Returns:
            Dictionary representation of the scene
        """
        return {
            "scene_id": str(scene.scene_id),
            "story_id": str(scene.story_id),
            "sequence": scene.sequence,
            "text": scene.text,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "created_at": scene.created_at.isoformat()
        }

    @staticmethod
    def from_story_response(response: StoryResponse) -> Dict[str, Any]:
        """Convert StoryResponse object to JSON data
        
        Args:
            response: StoryResponse object
            
        Returns:
            Dictionary representation of the response
        """
        return {
            "status": response.status,
            "story_id": str(response.story_id),
            "title": response.title,
            "created_at": response.created_at.isoformat()
        }

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
