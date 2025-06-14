import asyncio
import logging
from typing import Dict, Any

from app.utils.validator import Validator
from app.utils.json_converter import JSONConverter
from app.core.celery_app import celery_app

from app.models.story_types import StoryRequest, StoryResponse
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
    """
    Celery task to generate a complete story with text, images, and audio.
    Uses run_in_executor to handle async operations within the task.
    
    Args:
        self: Celery task instance.
        story_id: ID of the story.
        request_dict: StoryRequest data as dictionary.
    
    Returns:
        Dictionary with the task result.
    """
    
    logger.info(f"[TASK] Starting story generation task for story_id={story_id}")

    # Run async story generation in a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    request = StoryRequest(**request_dict)
    logger.debug(f"[TASK] Request received: prompt='{request.prompt[:50]}...', "
                 f"style='{request.style}', num_scenes={request.num_scenes}")
    
    # Run async operation synchronously
    result = loop.run_until_complete(generate_story_async(story_id, request))
    
    # Clean up event loop
    loop.close()
    
    # Validate model data before conversion (story completion)
    Validator.validate_model_data(result, is_completion=True)
    
    # Convert result to StoryResponse object
    response = JSONConverter.parse_json(result, StoryResponse)
    
    if response.status == "success":
        logger.info(f"[TASK] Story generation successful for story_id={story_id}")
    else:
        logger.error(f"[TASK] Story generation failed for story_id={story_id}: {response.error}")

    return JSONConverter.from_story_response(response)
