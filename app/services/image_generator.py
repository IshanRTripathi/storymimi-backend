import logging
from typing import Dict

from app.database.supabase_client import StorageService
from app.models.story_types import StoryStatus, StoryRequest
from app.services.ai_service import AIService
from app.services.story_extractor import StoryExtractor
from app.services.image_generator_services import ImageGeneratorService

logger = logging.getLogger(__name__)

# right now story_generator.py handles both storyline and image prompt generation, 
# we can delegate the image promt generation to this

@staticmethod
def generate_image_prompt(scene_text: str) -> str:
    """Generate an image prompt from scene text
    
    Args:
        scene_text: The text content of the scene
        
    Returns:
        A formatted image prompt
    """
    # Extract key elements from the scene text
    first_sentence = scene_text.split(".")[0].strip()
    if not first_sentence:
        first_sentence = scene_text[:50]
        
    # Add descriptive keywords
    keywords = ["illustration", "visual", "scene", "depiction"]
    return f"{', '.join(keywords)} of: {first_sentence}..."