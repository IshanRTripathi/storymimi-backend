from typing import Dict, List, Optional, Any
import logging
from app.models.story_types import StoryStatus, Scene
from app.utils.json_converter import JSONConverter

logger = logging.getLogger(__name__)

class StoryExtractor:
    """Handles extraction and validation of story data from AI responses"""
    
    @staticmethod
    def parse_story_json(story_text: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from AI response
        
        Args:
            story_text: The raw AI response text
            
        Returns:
            Parsed JSON data or None if parsing fails
        """
        try:
            data = JSONConverter.parse_json(story_text, Dict[str, Any])
            logger.debug("Successfully parsed story JSON")
            return data
        except ValueError as e:
            logger.warning(f"AI returned invalid JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing story JSON: {str(e)}")
            return None

    @staticmethod
    def extract_scenes_from_text(text: str, num_scenes: int = 5) -> List[Scene]:
        """Extract scenes from plain text story
        
        Args:
            text: The raw story text
            num_scenes: Number of scenes to extract
            
        Returns:
            List of Scene objects
        """
        # Split text into chunks based on natural breaks
        chunks = text.split('\n\n')
        scene_size = max(len(chunks) // num_scenes, 1)
        scenes = []
        
        for i in range(0, len(chunks), scene_size):
            scene_text = ' '.join(chunks[i:i + scene_size])
            scenes.append(Scene(
                text=scene_text,
                image_prompt=f"An illustration for: {scene_text[:100]}..."
            ))
            
            # Stop if we have enough scenes
            if len(scenes) >= num_scenes:
                break
                
        return scenes[:num_scenes]

    @staticmethod
    def extract_story_data(story_text: str, num_scenes: int = 5) -> Dict[str, Any]:
        """Extract story data from AI response
        
        Args:
            story_text: The raw AI response text
            num_scenes: Number of scenes to extract
            
        Returns:
            Story data in the expected format
        """
        data = StoryExtractor.parse_story_json(story_text)
        
        if not data:
            # Fallback to plain text extraction
            scenes = StoryExtractor.extract_scenes_from_text(story_text, num_scenes)
            return {
                "title": "Untitled",
                "scenes": [scene.to_dict() for scene in scenes]
            }
            
        # Validate and clean data
        title = data.get("title", "Untitled")
        scenes = data.get("scenes", [])
        
        # Ensure we have the required number of scenes
        if len(scenes) < num_scenes:
            additional_scenes = StoryExtractor.extract_scenes_from_text(story_text, num_scenes - len(scenes))
            scenes.extend([scene.to_dict() for scene in additional_scenes])
            
        # Ensure each scene has required fields
        for scene in scenes:
            if "text" not in scene:
                scene["text"] = ""
            if "image_prompt" not in scene:
                scene["image_prompt"] = f"An illustration for: {scene['text'][:100]}..."
            
        # Convert scenes back to dictionaries
        scene_dicts = [scene.to_dict() for scene in scenes]
        
        return {
            "title": title,
            "scenes": scene_dicts[:num_scenes]
        }

    @staticmethod
    def get_story_status(error: Optional[Exception] = None) -> StoryStatus:
        """Get appropriate story status based on error
        
        Args:
            error: Optional error that occurred
            
        Returns:
            Appropriate StoryStatus
        """
        if error:
            logger.error(f"Story processing error: {str(error)}")
            return StoryStatus.FAILED
        return StoryStatus.COMPLETE
