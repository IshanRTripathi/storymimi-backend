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
from datetime import datetime, timezone

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

    async def generate_story(self, request: StoryRequest, story_id: str) -> Dict[str, Any]:
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
        prompt = getattr(request, "prompt", "default prompt")
        
        now = datetime.now().isoformat()
        for i in range(num_scenes):  
            scene = {
                "scene_id": str(uuid.uuid4()),
                "story_id": story_id,
                "sequence": i,
                "text": f"Scene {i+1}: {prompt}",
                "title": f"Scene {i+1}",
                "image_prompt": f"An illustration for: {prompt}",
                "image_url": f"https://example.com/image_{i}.png",
                "audio_url": f"https://example.com/audio_{i}.mp3",
                "created_at": now,
                "updated_at": now
            }
            scenes.append(scene)
        
        logger.info(f"[MOCK] Generated {len(scenes)} scenes")
        
        # Generate mock story metadata
        story_metadata = {
            "child_profile": {
                "name": "Mock Child",
                "age": 5,
                "gender": "any",
                "personality": ["curious", "friendly"],
                "fears": ["none"],
                "favorites": {
                    "animal": "dog",
                    "color": "blue",
                    "toy": "ball"
                },
                "physical_appearance": {
                    "height": "average",
                    "build": "normal",
                    "skin_tone": "any",
                    "hair_style": "simple",
                    "hair_length": "medium",
                    "hair_color": "brown",
                    "accessories": ["none"],
                    "clothing": {
                        "top": "t-shirt",
                        "bottom": "pants",
                        "shoes": "sneakers"
                    }
                }
            },
            "side_character": {
                "exists": True,
                "description": "A friendly companion"
            },
            "story_meta": {
                "value_to_teach": "friendship",
                "setting_description": "a magical world",
                "scene_count": num_scenes,
                "tone": "warm and friendly",
                "story_title": getattr(request, "title", "Mock Story")
            }
        }
        
        return {
            "story_id": story_id,
            "title": getattr(request, "title", "Mock Story"),
            "status": "COMPLETED",  # Using a valid status from StoryStatus enum
            "scenes": scenes,
            "user_id": str(request.user_id),
            "story_metadata": story_metadata,  # Add the story metadata
            "created_at": now,
            "updated_at": now
        }
    
    async def generate_structured_story(self, user_input: str) -> Dict[str, Any]:
        """Mock structured story generation."""
        logger.info(f"[MOCK] Generating structured story for input: {user_input[:50]}...")
        await asyncio.sleep(self.delay_seconds)
        return {
            "child_profile": {
                "name": "Lily",
                "age": 5,
                "gender": "female",
                "personality": ["curious", "brave", "kind", "creative"],
                "fears": ["darkness", "loud noises"],
                "favorites": {"animal": "bunny", "color": "pink", "toy": "doll"},
                "physical_appearance": {
                    "height": "small",
                    "build": "slender",
                    "skin_tone": "fair",
                    "hair_style": "braids",
                    "hair_length": "long",
                    "hair_color": "brown",
                    "accessories": ["headband"],
                    "clothing": {"top": "dress", "bottom": "leggings", "shoes": "sneakers"}
                }
            },
            "side_character": {
                "exists": True,
                "description": "A small, fluffy, blue bunny named Patches",
                "relationship_to_main": "loyal companion and confidant",
                "growth_arc": "learns to be brave alongside Lily"
            },
            "story_meta": {
                "value_to_teach": "kindness",
                "setting_description": "a whimsical forest",
                "scene_count": 3,
                "tone": "warm and magical",
                "story_title": f"The Magical Journey of Lily and {user_input.split()[0] if user_input else 'Friend'}",
                "target_age_range": "4-6",
                "difficulty_level": "beginner",
                "educational_concepts": ["friendship", "bravery", "helping others"],
                "emotional_themes": ["empathy", "courage", "joy"],
                "content_warnings": [],
                "readability_score": "age-appropriate"
            },
            "scenes": [
                {
                    "scene_number": 1,
                    "text": "Lily, a curious girl, ventured into the Whispering Woods with her best friend, Patches the blue bunny.",
                    "prev_scene_summary": "",
                    "time_of_day": "bright morning",
                    "emotional_arc": "excitement and anticipation",
                    "learning_checkpoints": ["identifying emotions", "recognizing curiosity"],
                    "character_development": {
                        "main_character_state": "curious and slightly nervous",
                        "side_character_state": "supportive and playful",
                        "relationship_progress": "established trust"
                    },
                    "vocabulary_highlights": ["ventured", "whispering", "curious"]
                },
                {
                    "scene_number": 2,
                    "text": "They discovered a hidden glade where glowing flowers bloomed, and a shy forest spirit greeted them.",
                    "prev_scene_summary": "Lily and Patches entered the magical forest together",
                    "time_of_day": "golden afternoon",
                    "emotional_arc": "wonder and gentle courage",
                    "learning_checkpoints": ["being gentle with others", "respecting nature"],
                    "character_development": {
                        "main_character_state": "fascinated and gentle",
                        "side_character_state": "protective and curious",
                        "relationship_progress": "growing confidence in each other"
                    },
                    "vocabulary_highlights": ["discovered", "glade", "bloomed", "spirit"]
                },
                {
                    "scene_number": 3,
                    "text": "Lily and Patches shared their snacks with the spirit, learning the joy of giving, and returned home with hearts full of new friends.",
                    "prev_scene_summary": "They met a shy forest spirit in a magical glade",
                    "time_of_day": "warm sunset",
                    "emotional_arc": "fulfillment and joy",
                    "learning_checkpoints": ["sharing with others", "making new friends"],
                    "character_development": {
                        "main_character_state": "confident and happy",
                        "side_character_state": "proud and content",
                        "relationship_progress": "strengthened friendship"
                    },
                    "vocabulary_highlights": ["shared", "spirit", "giving", "hearts"]
                }
            ]
        }
    
    async def generate_visual_profile(self, child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
        """Mock visual profile generation."""
        logger.info("[MOCK] Generating visual profile...")
        await asyncio.sleep(self.delay_seconds)
        return {
            "character_prompt": {
                "appearance_description": "A small girl with long brown braids and a pink flowery dress",
                "emotional_state": "bright-eyed and cheerful expression",
                "posture_and_movement": "light and bouncy steps with graceful movements",
                "lighting_preferences": "soft warm light highlighting her face",
                "consistent_elements": ["braided hair", "headband", "dress flow", "cheerful smile"]
            },
            "side_character_prompt": {
                "appearance_description": "A fluffy blue bunny with floppy ears and a white cotton tail",
                "relationship_positioning": "usually close to Lily's side or slightly ahead",
                "movement_style": "gentle hops and playful bounces",
                "visual_personality": "attentive ears, expressive eyes, protective stance"
            },
            "scene_composition_guidelines": {
                "character_positioning": "Lily centered or slightly off-center with Patches nearby",
                "perspective_preferences": "eye-level or slightly elevated angle",
                "space_utilization": "characters occupy lower two-thirds of frame",
                "background_integration": "characters stand out against softer background elements"
            },
            "color_palette": {
                "primary_colors": ["soft pink", "sky blue", "forest green"],
                "accent_colors": ["golden yellow", "lavender purple"],
                "mood_specific_variations": {
                    "happy": "brighter and warmer",
                    "calm": "softer and cooler",
                    "excited": "more vibrant and saturated"
                }
            }
        }
    
    async def generate_base_style(self, setting: str, tone: str) -> str:
        """Mock base style generation."""
        logger.info("[MOCK] Generating base style...")
        await asyncio.sleep(self.delay_seconds)
        return {
            "base_style": {
                "art_style": "ghibli",
                "lighting": {
                    "primary_source": "soft natural sunlight",
                    "secondary_sources": "magical glows and sparkles",
                    "mood_lighting": "warm golden highlights",
                    "time_of_day_variations": "morning brightness to evening warmth"
                },
                "atmosphere": {
                    "overall_mood": "whimsical and gentle",
                    "weather_elements": "light breeze with floating leaves",
                    "particle_effects": "subtle sparkles and glowing orbs",
                    "depth_treatment": "layered forest elements with atmospheric perspective"
                },
                "color_scheme": {
                    "primary_palette": "forest greens and sky blues",
                    "accent_colors": "golden yellows and soft purples",
                    "mood_variations": "warmer for joyful moments, cooler for calm scenes"
                },
                "composition_rules": {
                    "layout_grid": "rule of thirds with dynamic diagonals",
                    "focal_points": "character expressions and magical elements",
                    "depth_layers": "detailed foreground, atmospheric background"
                }
            }
        }

    async def generate_scene_moment(self, scene_text: str, story_so_far: str = "") -> str:
        """Mock scene moment generation."""
        logger.info("[MOCK] Generating scene moment...")
        await asyncio.sleep(self.delay_seconds)
        return {
            "scene_moment": {
                "primary_action": "Lily reaching out to touch a glowing flower",
                "character_emotions": {
                    "main_character": "wonder and gentle curiosity in her eyes",
                    "side_character": "protective alertness with perked ears"
                },
                "spatial_arrangement": {
                    "character_positioning": "Lily kneeling in foreground, Patches close behind",
                    "environmental_interaction": "hands near glowing flora, feet on mossy ground",
                    "depth_placement": "characters in foreground, magical elements in mid-ground"
                },
                "visual_emphasis": {
                    "focal_point": "the interaction between hand and glowing flower",
                    "supporting_elements": "floating sparkles and swirling leaves",
                    "emotional_enhancers": "soft magical glow illuminating faces"
                },
                "temporal_context": {
                    "time_of_day": "golden afternoon light",
                    "weather_mood": "calm and clear with gentle breeze",
                    "season_hints": "late spring blooms and fresh leaves"
                },
                "educational_integration": {
                    "learning_elements": "careful observation of nature",
                    "value_reinforcement": "gentle and respectful interaction with environment"
                }
            }
        }
    
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
        
        try:
            with open(image_file, "rb") as f:
                content = f.read()
                if not content or len(content) < 100:
                    logger.error(f"Invalid image file {image_file}: too small or empty")
                    raise ValueError("Invalid image data")
                logger.debug(f"Successfully read image file with size: {len(content)} bytes")
                return content
        except Exception as e:
            logger.error(f"Failed to read image file {image_file}: {str(e)}")
            raise
    
    async def generate_audio(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> bytes:
        """Mock audio generation that returns a sample audio file after a delay
        
        Args:
            text: The text to convert to speech
            voice_id: The voice ID to use
            
        Returns:
            Sample audio bytes from the mock data directory
            
        Raises:
            ValueError: If audio generation fails
        """
        logger.info(f"[MOCK] Generating audio with V3 simulation for text length: {len(text)}")
        logger.debug(f"[MOCK] Using voice_id: {voice_id}")
        
        # Simulate processing delay
        await asyncio.sleep(self.delay_seconds)
        
        # Get a list of all audio files in the mock data directory
        audio_files = list((MOCK_DATA_DIR / "audio").glob("*.mp3"))
        
        if not audio_files:
            logger.error("[MOCK] No sample audio files found")
            raise ValueError("No sample audio files available")
        
        # Choose a random audio file and read its contents
        audio_file = random.choice(audio_files)
        logger.debug(f"[MOCK] Selected audio file: {audio_file.name}")
        
        try:
            with open(audio_file, "rb") as f:
                content = f.read()
                if not content or len(content) < 100:
                    logger.error(f"[MOCK] Invalid audio file {audio_file}: too small or empty")
                    raise ValueError("Invalid audio data")
                    
                logger.info(f"[MOCK] Successfully read audio file, size: {len(content)} bytes")
                return content
                
        except Exception as e:
            logger.error(f"[MOCK] Failed to read audio file {audio_file}: {str(e)}")
            raise ValueError(f"Failed to read audio file: {str(e)}")