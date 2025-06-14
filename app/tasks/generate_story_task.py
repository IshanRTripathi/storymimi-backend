import asyncio
import logging
from typing import Dict, Any

from app.utils.story_validator import validate_story_data
from app.utils.json_converter import JSONConverter
from app.core.celery_app import celery_app

from app.models.story import StoryRequest, StoryResponse
from app.services.story_generator import generate_story_async

# Setup logger
logger = logging.getLogger(__name__)

# Assuming celery_app is globally available (typically in a shared module)


@celery_app.task(bind=True, name="generate_story_task")
def generate_story_task(self, story_id: str, request_dict: Dict[str, Any]):
    """
    Celery task to generate a complete story with text, images, and audio.

    Args:
        self: Celery task instance.
        story_id: ID of the story.
        request_dict: StoryRequest data as dictionary.

    Returns:
        Dictionary with the task result.
    """
    logger.info(f"[TASK] Starting story generation task for story_id={story_id}")

    loop = asyncio.get_event_loop()
    request = StoryRequest(**request_dict)

    logger.debug(f"[TASK] Request received: prompt='{request.prompt[:50]}...', "
                 f"style='{request.style}', num_scenes={request.num_scenes}")

    result = loop.run_until_complete(generate_story_async(story_id, request))
    
    # Convert result to StoryResponse object
    response = JSONConverter.parse_json(result, StoryResponse)
    
    if response.status == "success":
        logger.info(f"[TASK] Story generation successful for story_id={story_id}")
    else:
        logger.error(f"[TASK] Story generation failed for story_id={story_id}: {response.error}")

    return JSONConverter.from_story_response(response)
