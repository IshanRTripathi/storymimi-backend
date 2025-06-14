import logging
from datetime import datetime
from typing import Dict

from app.database.supabase_client import SupabaseClient
from app.models.story import StoryStatus, StoryRequest
from app.models.story_entities import Story, Scene, StoryResponse
from app.services.ai_service import AIService
from app.services.story_extractor import StoryExtractor
from app.utils.json_converter import JSONConverter

logger = logging.getLogger(__name__)


async def generate_story_async(story_id: str, request: StoryRequest) -> Dict[str, str]:
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
            prompt = build_generation_prompt(request)
            logger.info(f"[GENERATOR] Generating story text via AIService for story_id={story_id}")
            story_text = await ai_service.generate_text(prompt)

            logger.debug(f"[GENERATOR] Raw AI output for story_id={story_id}: {story_text[:250]}...")

            # Parse raw data into entities
            story_data = StoryExtractor.extract_story_data(story_text, request.num_scenes)
            scenes = [
                Scene(
                    text=s["text"],
                    image_prompt=s.get("image_prompt", f"An illustration for: {s['text'][:100]}...")
                )
                for s in story_data["scenes"]
            ]

            if not scenes:
                raise ValueError("No scenes extracted from AI response")

            logger.info(f"[GENERATOR] Extracted {len(scenes)} scenes for story_id={story_id}")

            story = Story(
                story_id=story_id,
                title=story_data.get("title", "Untitled"),
                scenes=scenes,
                status=StoryStatus.PROCESSING.value,
                user_id=request.user_id,
                created_at=datetime.now().isoformat()
            )

            for i, scene in enumerate(story.scenes):
                logger.info(f"[GENERATOR] Processing scene {i+1}/{len(story.scenes)}")
                logger.debug(f"[GENERATOR] Generating image for scene {i+1}")

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

                logger.info(f"[GENERATOR] Scene {i+1} created successfully")

            await db_client.update_story_status(story_id, StoryStatus.COMPLETE)
            logger.info(f"[GENERATOR] Story generation completed for story_id={story_id}")

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
        logger.exception(f"[GENERATOR] Error occurred for story_id={story_id}")
        await db_client.update_story_status(story_id, StoryStatus.FAILED)
        # Handle error case
        await db_client.update_story_status(story_id, StoryStatus.FAILED)
        response = StoryResponse(
            status="error",
            story_id=story_id,
            title="Untitled",
            error=str(e)
        )
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
