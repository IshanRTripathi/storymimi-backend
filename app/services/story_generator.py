import logging
from datetime import datetime
from typing import Dict, Any

from app.database.supabase_client import SupabaseClient
from app.models.story_types import StoryStatus, StoryRequest, StoryResponse, Scene
from app.services.ai_service import AIService
from app.services.story_extractor import StoryExtractor
from app.services.story_processor import StoryProcessor
from app.utils.json_converter import JSONConverter
from app.utils.validator import Validator

logger = logging.getLogger(__name__)


async def generate_story_async(story_id: str, request: StoryRequest) -> Dict[str, Any]:
    """
    Async function to generate a complete story with text, images, and audio.

    Args:
        story_id: The ID of the story to generate.
        request: The StoryRequest object.

    Returns:
        A dictionary with the task result.
    """
    db_client = SupabaseClient()
    logger.info(f"[GENERATOR] Started generation for story_id={story_id}")

    try:
        await db_client.update_story_status(story_id, StoryStatus.PROCESSING)

        async with AIService() as ai_service:
            # Get and validate AI-generated story content
            story_data = await ai_service.generate_story(request)
            Validator.validate_ai_response(story_data)
            
            if not story_data.get("scenes"):
                raise ValueError("No scenes extracted from AI response")
                
            logger.info(f"[GENERATOR] Created {len(story_data['scenes'])} scenes for story_id={story_id}")
        
        # Create scenes from processed JSON data
        logger.info(f"[GENERATOR] Creating scenes for story_id={story_id}")
        try:
            scenes = [
                Scene(
                    title=f"Scene {i+1}",
                    description=s["text"],
                    text=s["text"],
                    image_prompt=s.get("image_prompt", f"An illustration for: {s['text'][:100]}...")
                )
                for i, s in enumerate(story_data["scenes"])
            ]
        except Exception as e:
            logger.error(f"[GENERATOR] Error creating scenes for story_id={story_id}: {str(e)}")
            raise
        logger.info(f"[GENERATOR] Created {len(scenes)} scenes for story_id={story_id}")
        
        # 3. Process each scene
        for i, scene in enumerate(scenes):
            logger.info(f"[GENERATOR] Processing scene {i+1}/{len(scenes)}")
            
            # 3.1 Generate image for scene
            logger.debug(f"[GENERATOR] Generating image for scene {i+1}")
            image_bytes = await ai_service.generate_image(
                scene.image_prompt,
                width=768,
                height=432
            )
            
            scene.image_url = await db_client.upload_image(story_id, i, image_bytes)
            logger.debug(f"[GENERATOR] Image URL: {scene.image_url}")
            
            # 3.2 Generate audio for scene
            logger.debug(f"[GENERATOR] Generating audio for scene {i+1}")
            audio_bytes = await ai_service.generate_audio(scene.text)
            scene.audio_url = await db_client.upload_audio(story_id, i, audio_bytes)
            logger.debug(f"[GENERATOR] Audio URL: {scene.audio_url}")
            
            # Create scene in database
            await db_client.create_scene(
                story_id=story_id,
                sequence=i,
                text=scene.text,
                image_url=scene.image_url,
                audio_url=scene.audio_url
            )
            
            logger.info(f"[GENERATOR] Scene {i+1} created successfully")
        
        # 4. Get the updated story from database
        logger.info(f"[GENERATOR] Fetching updated story from database for story_id={story_id}")
        story = await db_client.get_story(story_id)
        if not story:
            raise ValueError(f"Story not found in database after completion: {story_id}")
            
        # Update story status to completed
        await db_client.update_story_status(story_id, StoryStatus.COMPLETED)
        
        logger.info(f"[GENERATOR] Story generated successfully for story_id={story_id}")
        
        # Create response with database data and scenes
        # Use the database story data directly, no need to create a new StoryResponse
        story_data = story.copy()
        story_data['scenes'] = [dict(scene) for scene in scenes]
        return story_data
        
        return JSONConverter.from_story_response(response)
        
    except Exception as e:
        logger.exception(f"[GENERATOR] Error occurred for story_id={story_id}")
        await db_client.update_story_status(story_id, StoryStatus.FAILED)
        
        # Get the actual story data from the database
        story_data = await db_client.get_story(story_id)
        response = StoryResponse(**story_data)
        response.error = str(e)
        response.status = StoryStatus.FAILED
        
        return JSONConverter.from_story_response(response)


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
