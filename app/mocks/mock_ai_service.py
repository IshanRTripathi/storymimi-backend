import asyncio
import logging
import os
import random
import json
import uuid
from uuid import UUID
from pathlib import Path
from typing import Optional, Dict, Any
from app.utils.validator import Validator
from app.models.story_types import StoryRequest

# Set up logging
logger = logging.getLogger(__name__)

# Get the path to the mock data directory
MOCK_DATA_DIR = Path(__file__).parent / "data"

class MockAIService:
    """Mock implementation of AIService that returns static data after a delay
    
    This class mimics the behavior of the real AIService but doesn't make actual API calls.
    Instead, it returns pre-defined sample data after a configurable delay to simulate
    network latency and processing time.
    """
    
    def __init__(self, delay_seconds: float = 5.0):
        """Initialize the mock service with a configurable delay
        
        Args:
            delay_seconds: The number of seconds to delay before returning results
        """
        self.delay_seconds = delay_seconds
        
        # Ensure the mock data directories exist
        self._ensure_mock_data_dirs()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def _ensure_mock_data_dirs(self):
        """Ensure that the mock data directories exist"""
        logger.debug("Ensuring mock data directories exist")
        
        # Create the main data directory if it doesn't exist
        os.makedirs(MOCK_DATA_DIR, exist_ok=True)
        
        # Create subdirectories for each type of data
        os.makedirs(MOCK_DATA_DIR / "text", exist_ok=True)
        os.makedirs(MOCK_DATA_DIR / "images", exist_ok=True)

    async def generate_story(self, request: StoryRequest) -> Dict[str, Any]:
        """Generate a mock story with scenes
        
        Args:
            request: StoryRequest object containing story request data
            
        Returns:
            Dictionary containing generated story data
        """
        logger.info("[MOCK] Generating story with prompt: %s", request.prompt)
        
        await asyncio.sleep(self.delay_seconds)
        
        # Generate mock scenes
        scenes = []
        num_scenes = getattr(request, "num_scenes", 3)
        story_id = str(request.story_id) if hasattr(request, "story_id") else str(uuid.uuid4())
        prompt = getattr(request, "prompt", "default prompt")
        
        for i in range(1, num_scenes + 1):
            scene = {
                "scene_id": str(uuid.uuid4()),
                "story_id": story_id,
                "sequence": i,
                "text": f"Scene {i}: {prompt}",
                "image_prompt": f"An illustration for: {prompt[:100]}...",
                "image_url": f"https://mock-image-url.com/story/{story_id}/scene/{i}",
                "audio_url": f"https://mock-audio-url.com/story/{story_id}/scene/{i}"
            }
            scenes.append(scene)
        
        return {
            "story_id": story_id,
            "title": getattr(request, "title", "Mock Story"),
            "status": "success",
            "scenes": scenes,
            "user_id": str(request.user_id)
        }
        os.makedirs(MOCK_DATA_DIR / "audio", exist_ok=True)
        
        logger.debug(f"Mock data directories created at {MOCK_DATA_DIR}")
    
    async def generate_text(self, prompt: str) -> str:
        """Mock text generation that returns a sample text after a delay
        
        Args:
            prompt: The prompt for text generation (ignored in mock)
            
        Returns:
            A sample text from the mock data directory
        """
        logger.debug(f"Mock generating text with prompt length: {len(prompt)}")
        
        # Simulate processing delay
        logger.debug(f"Simulating processing delay of {self.delay_seconds} seconds")
        await asyncio.sleep(self.delay_seconds)
        
        # Get a list of all text files in the mock data directory (both .txt and .json)
        text_files = list((MOCK_DATA_DIR / "text").glob("*.txt")) + \
                    list((MOCK_DATA_DIR / "text").glob("*.json"))
        logger.debug(f"Found {len(text_files)} sample text files in mock data directory")
        
        # If no text files exist, return a default text
        if not text_files:
            logger.debug("No sample text files found, returning default text")
            default_text = (
                "Once upon a time in a magical forest, a young adventurer named Lily discovered "
                "a hidden path leading to an ancient temple. The temple was guarded by mystical "
                "creatures who tested her courage and wisdom. After solving their riddles, "
                "Lily was granted access to the temple's inner chamber, where she found a "
                "glowing crystal that could heal the sick forest. With the crystal in hand, "
                "Lily returned to her village as a hero, bringing life back to the dying trees "
                "and animals."
            )
            return default_text
        
        # Choose a random text file and read its contents
        text_file = random.choice(text_files)
        logger.debug(f"Selected random text file: {text_file.name}")
        
        with open(text_file, "r", encoding="utf-8") as f:
            content = f.read()
            logger.debug(f"Successfully read text file with content length: {len(content)}")
            
            # If it's a JSON file, return the content as is
            if text_file.suffix == '.json':
                try:
                    data = json.loads(content)
                    logger.debug("Successfully parsed JSON data")
                    
                    # Validate story data structure
                    Validator.validate_ai_response(data)
                    
                    # Return only AI-generated content
                    return data
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON, returning raw content")
                    return content
            
            return content
    
    async def generate_image(self, prompt: str, width: int = 768, height: int = 432, 
                           steps: int = 12, seed: Optional[int] = None) -> bytes:
        """Mock image generation that returns a sample image after a delay
        
        Args:
            prompt: The prompt for image generation (ignored in mock)
            width: The width of the image (ignored in mock)
            height: The height of the image (ignored in mock)
            steps: The number of steps for generation (ignored in mock)
            seed: The random seed (ignored in mock)
            
        Returns:
            Sample image bytes from the mock data directory
        """
        logger.debug(f"Mock generating image with prompt length: {len(prompt)}, dimensions: {width}x{height}")
        
        # Simulate processing delay
        logger.debug(f"Simulating processing delay of {self.delay_seconds} seconds")
        await asyncio.sleep(self.delay_seconds)
        
        # Get a list of all image files in the mock data directory
        image_files = list((MOCK_DATA_DIR / "images").glob("*.jpg")) + \
                     list((MOCK_DATA_DIR / "images").glob("*.png"))
        logger.debug(f"Found {len(image_files)} sample image files in mock data directory")
        
        # If no image files exist, create a simple colored image
        if not image_files:
            logger.debug("No sample image files found, returning default 1x1 pixel image")
            # Return a simple 1x1 pixel PNG image (red color)
            default_image = bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
                "89000000017352474200aece1ce90000000467414d410000b18f0bfc61050000"
                "000c49444154789c636060606000000005000001a5f645380000000049454e44ae426082"
            )
            return default_image
        
        # Choose a random image file and read its contents
        image_file = random.choice(image_files)
        logger.debug(f"Selected random image file: {image_file.name}")
        
        with open(image_file, "rb") as f:
            content = f.read()
            logger.debug(f"Successfully read image file with size: {len(content)} bytes")
            return content
    
    async def generate_audio(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> bytes:
        """Mock audio generation that returns a sample audio file after a delay
        
        Args:
            text: The text to convert to speech (ignored in mock)
            voice_id: The voice ID to use (ignored in mock)
            
        Returns:
            Sample audio bytes from the mock data directory
        """
        logger.debug(f"Mock generating audio for text of length: {len(text)}, voice_id: {voice_id}")
        
        # Simulate processing delay
        logger.debug(f"Simulating processing delay of {self.delay_seconds} seconds")
        await asyncio.sleep(self.delay_seconds)
        
        # Get a list of all audio files in the mock data directory
        audio_files = list((MOCK_DATA_DIR / "audio").glob("*.mp3")) + \
                     list((MOCK_DATA_DIR / "audio").glob("*.wav"))
        logger.debug(f"Found {len(audio_files)} sample audio files in mock data directory")
        
        # If no audio files exist, return a simple audio file
        if not audio_files:
            logger.debug("No sample audio files found, returning default empty MP3")
            # Return a simple empty MP3 file (not actually playable)
            default_audio = bytes.fromhex(
                "494433030000000000545432000000000054414c42000000000000"
            )
            return default_audio
        
        # Choose a random audio file and read its contents
        audio_file = random.choice(audio_files)
        logger.debug(f"Selected random audio file: {audio_file.name}")
        
        with open(audio_file, "rb") as f:
            content = f.read()
            logger.debug(f"Successfully read audio file with size: {len(content)} bytes")
            return content