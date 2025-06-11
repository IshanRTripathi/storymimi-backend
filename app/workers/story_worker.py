import asyncio
import json
import logging
from typing import Dict, Any, List
from uuid import UUID

from app.workers.celery_app import celery_app
from app.database.supabase_client import SupabaseClient
from app.services.ai_service_mock_adapter import AIServiceFactory
from app.models.story import StoryStatus, StoryRequest

# Set up logging
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="generate_story_task")
def generate_story_task(self, story_id: str, request_dict: Dict[str, Any]):
    """Celery task to generate a complete story with text, images, and audio
    
    Args:
        self: The Celery task instance
        story_id: The ID of the story to generate
        request_dict: The StoryRequest data as a dictionary
        
    Returns:
        A dictionary with the task result
    """
    logger.info(f"Starting story generation task for story_id={story_id}")
    
    # Create an event loop for async operations
    loop = asyncio.get_event_loop()
    
    # Convert the request dictionary back to a StoryRequest object
    request = StoryRequest(**request_dict)
    logger.debug(f"Story request: prompt='{request.prompt[:50]}...', style='{request.style}', num_scenes={request.num_scenes}")
    
    # Run the async story generation process
    result = loop.run_until_complete(_generate_story(story_id, request))
    
    if result.get("status") == "success":
        logger.info(f"Successfully completed story generation for story_id={story_id}")
    else:
        logger.error(f"Failed to generate story for story_id={story_id}: {result.get('error', 'Unknown error')}")
        
    return result

async def _generate_story(story_id: str, request: StoryRequest) -> Dict[str, Any]:
    """Async function to generate a complete story with text, images, and audio
    
    Args:
        story_id: The ID of the story to generate
        request: The StoryRequest object
        
    Returns:
        A dictionary with the task result
    """
    db_client = SupabaseClient()
    
    try:
        logger.info(f"Starting async story generation for story_id={story_id}")
        
        # Update story status to PROCESSING
        await db_client.update_story_status(story_id, StoryStatus.PROCESSING)
        logger.debug(f"Updated story status to PROCESSING for story_id={story_id}")
        
        # Generate the full story text
        async with await AIServiceFactory.create_service() as ai_service:
            # Create a prompt for the story generation
            story_prompt = f"""Create a {request.style if request.style else 'engaging'} story with {request.num_scenes} scenes based on the following prompt: {request.prompt}. 
            The story should have a clear beginning, middle, and end. 
            Format your response as a JSON object with the following structure:
            {{
                "title": "The title of the story",
                "scenes": [
                    {{
                        "text": "The text content of scene 1",
                        "image_prompt": "A detailed prompt to generate an image for scene 1"
                    }},
                    // Additional scenes...
                ]
            }}
            """
            
            logger.info(f"Generating story text for story_id={story_id}")
            # Generate the story text
            story_text = await ai_service.generate_text(story_prompt)
            logger.debug(f"Received story text response of length {len(story_text)} for story_id={story_id}")
            
            # Parse the JSON response
            try:
                story_data = json.loads(story_text)
                logger.debug(f"Successfully parsed story text as JSON for story_id={story_id}")
            except json.JSONDecodeError:
                logger.warning(f"Initial JSON parsing failed for story_id={story_id}, attempting to extract JSON from text")
                # If the response is not valid JSON, try to extract JSON from the text
                import re
                json_match = re.search(r'\{\s*"title".*\}\s*\}', story_text, re.DOTALL)
                if json_match:
                    try:
                        story_data = json.loads(json_match.group(0))
                        logger.debug(f"Successfully extracted and parsed JSON from text for story_id={story_id}")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse extracted JSON for story_id={story_id}")
                        raise Exception("Failed to parse story text as JSON")
                else:
                    logger.error(f"Could not find JSON pattern in text for story_id={story_id}")
                    raise Exception("Failed to parse story text as JSON")
            
            # Process each scene
            scenes = story_data.get("scenes", [])
            logger.info(f"Processing {len(scenes)} scenes for story_id={story_id}")
            
            for i, scene in enumerate(scenes):
                logger.debug(f"Processing scene {i+1}/{len(scenes)} for story_id={story_id}")
                
                # Generate image for the scene
                image_prompt = scene.get("image_prompt", f"An illustration for: {scene['text'][:100]}...")
                logger.debug(f"Generating image for scene {i+1} with prompt: '{image_prompt[:50]}...'")
                image_bytes = await ai_service.generate_image(image_prompt)
                
                # Generate audio for the scene
                logger.debug(f"Generating audio for scene {i+1} with text length: {len(scene['text'])}")
                audio_bytes = await ai_service.generate_audio(scene["text"])
                
                # Upload image and audio to Supabase Storage
                logger.debug(f"Uploading image for scene {i+1} to storage")
                image_url = await db_client.upload_image(story_id, i, image_bytes)
                
                logger.debug(f"Uploading audio for scene {i+1} to storage")
                audio_url = await db_client.upload_audio(story_id, i, audio_bytes)
                
                # Create a new scene record in the database
                logger.debug(f"Creating database record for scene {i+1}")
                await db_client.create_scene(
                    story_id=story_id,
                    sequence=i,
                    text=scene["text"],
                    image_url=image_url,
                    audio_url=audio_url
                )
                logger.info(f"Completed processing for scene {i+1}/{len(scenes)} for story_id={story_id}")
        
        # Update the story status to COMPLETE
        logger.info(f"All scenes processed successfully, updating status to COMPLETE for story_id={story_id}")
        await db_client.update_story_status(story_id, StoryStatus.COMPLETE)
        
        return {"status": "success", "story_id": story_id}
    except Exception as e:
        # Log the error
        logger.error(f"Error generating story for story_id={story_id}: {str(e)}", exc_info=True)
        
        # Update the story status to FAILED
        logger.info(f"Updating status to FAILED for story_id={story_id}")
        await db_client.update_story_status(story_id, StoryStatus.FAILED)
        
        # Return the error
        return {"status": "error", "story_id": story_id, "error": str(e)}