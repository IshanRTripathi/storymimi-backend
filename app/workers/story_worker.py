import asyncio
import logging
from typing import Dict, Any

from app.models.story_types import StoryRequest, StoryStatus
from app.services.ai_service import AIService
from app.services.story_extractor import StoryExtractor
from app.database.supabase_client import SupabaseClient
from app.utils.validator import Validator
from app.utils.json_converter import JSONConverter

logger = logging.getLogger(__name__)


async def generate_story_async(story_id: str, request: StoryRequest) -> Dict[str, Any]:
    """
    Async function to handle story generation with AI + uploads.

    Args:
        story_id: The ID of the story to generate.
        request: The StoryRequest object.

    Returns:
        A dictionary with the task result.
    """
    logger.info(f"[WORKER] Starting story generation for story_id={story_id}")
    
    try:
        db_client = SupabaseClient()
        
        # Update status to processing
        await db_client.update_story_status(story_id, StoryStatus.PROCESSING)
        
        async with AIService() as ai_service:
            prompt = StoryExtractor.build_generation_prompt(request)
            logger.info(f"[WORKER] Generating story text via AIService for story_id={story_id}")
            story_text = await ai_service.generate_text(prompt)
            
            logger.debug(f"[WORKER] Raw AI output for story_id={story_id}: {story_text[:250]}...")
            
            # Parse and validate AI response
            story_data = StoryExtractor.extract_story_data(story_text, request.num_scenes)
            Validator.validate_ai_response(story_data)
            
            if not story_data.get("scenes"):
                raise ValueError("No scenes extracted from AI response")
            
            logger.info(f"[WORKER] Extracted {len(story_data['scenes'])} scenes for story_id={story_id}")
            
            # Create story object
            story = Story(
                story_id=story_id,
                title=story_data.get("title", "Untitled"),
                scenes=[
                    Scene(
                        text=s["text"],
                        image_prompt=s.get("image_prompt", f"An illustration for: {s['text'][:100]}...")
                    )
                    for s in story_data["scenes"]
                ],
                status=StoryStatus.PROCESSING,
                user_id=request.user_id,
                created_at=datetime.now().isoformat()
            )
            
            # Process scenes
            for i, scene in enumerate(story.scenes):
                logger.info(f"[WORKER] Processing scene {i+1}/{len(story.scenes)}")
                
                # Generate media
                image_bytes = await ai_service.generate_image(scene.image_prompt)
                audio_bytes = await ai_service.generate_audio(scene.text)
                
                # Update scene with media URLs
                scene.image_url = await db_client.upload_image(story_id, i, image_bytes)
                scene.audio_url = await db_client.upload_audio(story_id, i, audio_bytes)
                
                # Create scene in database
                await db_client.create_scene(
                    story_id=story_id,
                    sequence=i,
                    text=scene.text,
                    image_url=scene.image_url,
                    audio_url=scene.audio_url
                )
                
                logger.info(f"[WORKER] Scene {i+1} created successfully")
            
            # Update story status to complete
            await db_client.update_story_status(story_id, StoryStatus.COMPLETE)
            
            # Create and return response
            response = StoryResponse(
                status="success",
                story_id=story_id,
                title=story.title
            )
            return JSONConverter.from_story_response(response)
            
    except Exception as e:
        logger.exception(f"[WORKER] Error occurred for story_id={story_id}")
        await db_client.update_story_status(story_id, StoryStatus.FAILED)
        response = StoryResponse(
            status="error",
            story_id=story_id,
            title="Untitled",
            created_at=datetime.now(),
            error=str(e)
        )
        return JSONConverter.from_story_response(response)
