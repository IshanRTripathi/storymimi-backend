import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from app.database.supabase_client import StoryRepository, StorageService
from app.models.story_types import StoryStatus, StoryRequest, StoryResponse, Scene
from app.services.ai_service import AIService
from app.services.story_extractor import StoryExtractor
from app.services.story_processor import StoryProcessor

from app.utils.json_converter import JSONConverter
from app.utils.validator import Validator
logger = logging.getLogger(__name__)


async def generate_story_async(story_id: str, request: StoryRequest, user_id: str) -> Dict[str, Any]:
    """
    Async function to generate a complete story with text, images, and audio.

    Args:
        story_id: The ID of the story to generate.
        request: The StoryRequest object.
        user_id: The ID of the user creating the story

    Returns:
        A dictionary with the task result.
    """
    try:
        # Initialize services
        db_client = StoryRepository()
        storage_service = StorageService()
        
        # Initialize story
        story = await initialize_story(db_client, request, story_id, user_id)   
        
        # Generate AI content
        async with AIService() as ai_service:
            scenes = await generate_scenes(ai_service, request, story_id)
            await process_scenes(db_client, storage_service, ai_service, story_id, scenes)
            
        # Complete story
        return await complete_story(db_client, story_id, scenes)
        
    except Exception as e:
        logger.exception(f"[GENERATOR] Error occurred for story_id={story_id}")
        return await handle_story_error(db_client, story_id, e)

async def initialize_story(db_client: StoryRepository, request: StoryRequest, story_id: str, user_id: str) -> Dict[str, Any]:
    """Initialize story in database and return story data."""
    logger.info(f"[GENERATOR] Started generation for story_id={story_id}")
    
    # Update story status
    await db_client.update_story_status(story_id, StoryStatus.PROCESSING)
    
    # Create story in database
    created_story = await db_client.create_story(
        title=request.title,
        prompt=request.prompt,
        user_id=request.user_id
    )
    
    if not created_story["story_id"]:
        raise ValueError("Failed to create story")
    
    # Get story data
    story_data = await db_client.get_story(created_story["story_id"])
    if not story_data:
        raise ValueError(f"Story not found: {created_story['story_id']}")
    
    # Add timestamps if not present
    if "created_at" not in story_data:
        story_data["created_at"] = datetime.utcnow().isoformat()
    story_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Add user_id if not present
    if "user_id" not in story_data:
        story_data["user_id"] = user_id
    
    return story_data

async def generate_scenes(ai_service: AIService, request: StoryRequest, story_id: str) -> List[Scene]:
    """Generate scenes using AI service."""
    ai_response = await ai_service.generate_story(request, story_id)
    Validator.validate_ai_response(ai_response)
    
    if not ai_response.get("scenes"):
        raise ValueError("No scenes extracted from AI response")
        
    logger.info(f"[GENERATOR] Created {len(ai_response['scenes'])} scenes for story_id={story_id}")
    logger.info(f"[GENERATOR] AI Response scene data: {ai_response}")
    return [
        Scene(
            scene_id=s['scene_id'],
            title=s['title'],
            text=s['text'],
            image_prompt=s['image_prompt'],
            image_url=s.get('image_url'),
            audio_url=s.get('audio_url'),
            created_at=s['created_at'],
            updated_at=s['updated_at']
        )
        for s in ai_response['scenes']
    ]

async def process_scenes(db_client: StoryRepository, storage_service: StorageService, 
                        ai_service: AIService, story_id: str, scenes: List[Scene]):
    """Process each scene including media generation and database storage."""
    logger.info(f"[GENERATOR] Creating scenes for story_id={story_id}")
    
    scene_dicts = []
    for i, scene in enumerate(scenes):
        await process_scene(db_client, storage_service, ai_service, story_id, i, scene)

async def process_scene(db_client: StoryRepository, storage_service: StorageService, 
                       ai_service: AIService, story_id: str, index: int, scene: Scene):
    """Process a single scene including media generation and database storage."""
    logger.info(f"[GENERATOR] Processing scene {index+1}")
    
    # Generate and upload media
    await generate_and_store_media(storage_service, ai_service, story_id, index, scene)
    
    # Create and update scene in database
    await create_and_update_scene(db_client, story_id, index, scene)

async def generate_and_store_media(storage_service: StorageService, ai_service: AIService, 
                                 story_id: str, index: int, scene: Scene):
    """Generate and store media (image and audio) for a scene."""
    # Generate and upload image
    logger.debug(f"[GENERATOR] Generating and uploading image for scene {index+1}")
    try:
        image_bytes = await ai_service.generate_image(scene.image_prompt)
        image_url = storage_service.upload_image(story_id, index, image_bytes)
        scene.image_url = image_url
        logger.debug(f"[GENERATOR] Image URL: {image_url}")
    except Exception as e:
        logger.error(f"[GENERATOR] Failed to process image: {str(e)}", exc_info=True)
        raise
    
    # Generate and upload audio
    logger.debug(f"[GENERATOR] Generating and uploading audio for scene {index+1}")
    try:
        audio_bytes = await ai_service.generate_audio(scene.text)
        audio_url = storage_service.upload_audio(story_id, index, audio_bytes)
        scene.audio_url = audio_url
        logger.debug(f"[GENERATOR] Audio URL: {audio_url}")
    except Exception as e:
        logger.error(f"[GENERATOR] Failed to process audio: {str(e)}", exc_info=True)
        raise

async def create_and_update_scene(db_client: StoryRepository, story_id: str, index: int, scene: Scene):
    """Create scene in database and update scene object with database data."""
    logger.info(f"[GENERATOR] Scene info: {scene}")
    
    # Create scene in database
    scene_data = await db_client.create_scene(
        story_id=story_id,
        sequence=index,
        text=scene.text,
        image_url=scene.image_url,
        audio_url=scene.audio_url
    )
    logger.info(f"[GENERATOR] Scene data: {scene_data}")
    # Update scene object with database data
    if scene_data:
        scene = Scene(
            scene_id=scene_data['scene_id'],
            title=scene_data['title'],
            text=scene_data['text'],
            image_prompt=scene_data['image_prompt'],
            image_url=scene_data.get('image_url'),
            audio_url=scene_data.get('audio_url'),
            created_at=scene_data['created_at'],
            updated_at=scene_data['updated_at']
        )
    
    logger.info(f"[GENERATOR] Scene {index+1} created successfully")

async def complete_story(db_client: StoryRepository, story_id: str, scenes: List[Scene]) -> Dict[str, Any]:
    """Complete story generation and return final response."""
    logger.info(f"[GENERATOR] Fetching updated story from database for story_id={story_id}")
    
    # Get updated story data
    story_data = await db_client.get_story(story_id)
    if not story_data:
        raise ValueError(f"Story not found in database after completion: {story_id}")
    
    # Update story status to completed
    await db_client.update_story_status(story_id, StoryStatus.COMPLETED)
    
    logger.info(f"[GENERATOR] Story generated successfully for story_id={story_id}")
    
    # Convert scenes to dictionaries before returning
    scene_dicts = []
    for scene in scenes:
        scene_dict = {
            "scene_id": str(scene.scene_id),
            "title": scene.title,
            "text": scene.text,
            "image_prompt": scene.image_prompt,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "created_at": scene.created_at if isinstance(scene.created_at, str) else datetime.now().isoformat(),
            "updated_at": scene.updated_at if isinstance(scene.updated_at, str) else datetime.now().isoformat()
        }
        scene_dicts.append(scene_dict)
    
    return {
        "story_id": story_data["story_id"],
        "title": story_data["title"],
        "status": StoryStatus.COMPLETED,
        "scenes": scene_dicts,
        "user_id": story_data["user_id"],
        "created_at": story_data["created_at"] if isinstance(story_data["created_at"], str) else datetime.now().isoformat(),
        "updated_at": story_data["updated_at"] if isinstance(story_data["updated_at"], str) else datetime.now().isoformat()
    }

async def handle_story_error(db_client: StoryRepository, story_id: str, error: Exception) -> Dict[str, Any]:
    """Handle story generation error and return error response."""
    await db_client.update_story_status(story_id, StoryStatus.FAILED)
    
    # Get the actual story data from the database
    story_data = await db_client.get_story(story_id)
    
    return {
        "story_id": story_data["story_id"],
        "title": story_data["title"],
        "status": StoryStatus.FAILED,
        "scenes": [],
        "user_id": story_data["user_id"],
        "created_at": story_data.get("created_at"),
        "updated_at": story_data.get("updated_at"),
        "error": str(error)
    }


@staticmethod
def build_generation_prompt(request: StoryRequest) -> str:
    """Build a prompt string for the AI story generator"""
    style = request.style if request.style else 'engaging'

    logger.debug(f"Building story prompt for style={style}, num_scenes={request.num_scenes}")
    return f"""You are a professional story writer and formatter. Your task is to generate a story in a specific JSON format.

IMPORTANT: You MUST return ONLY the JSON object. Do not include any additional text or explanations.

Prompt: {request.prompt}
Style: {style}
Number of Scenes: {request.num_scenes}

JSON Format Requirements:
1. Use ONLY double quotes for JSON
2. No spaces between property names and values
3. No extra text or explanations
4. No comments or markdown
5. No emojis or special characters
6. No HTML or markdown formatting

Example output:
{{"title":"The Adventure Begins","scenes":[{{"text":"The sun was setting over the distant mountains as Sarah prepared for her journey.","image_prompt":"A lone figure standing at the edge of a cliff, mountains in the background, sunset"}}]}}

Remember:
1. Return ONLY the JSON object
2. Use proper JSON format with double quotes
3. Include both text and image_prompt for each scene
4. Make sure the title and scenes array are present
5. No additional text or explanations allowed
"""
