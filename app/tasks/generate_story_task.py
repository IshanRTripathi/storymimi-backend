import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from app.utils.validator import Validator
from app.core.celery_app import celery_app
from app.models.story_types import StoryStatus, StoryRequest
from app.services.story_generator import generate_story_async

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="story_task.generate")
def generate_story_task(self, story_id: str, request_dict: Dict[str, Any], user_id: str):
    """Story generation task using async implementation."""
    try:
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Get request
        request = StoryRequest(**request_dict)
        logger.info(f"[TASK] Starting story generation for story_id={story_id}")
        logger.debug(f"[TASK] Request: {request}")
        # Generate story using async flow
        result = loop.run_until_complete(generate_story_async(story_id, request, user_id))
        logger.debug(f"[TASK] Raw result: {result}")
        # Validate result
        Validator.validate_model_data(result, is_completion=True)
        logger.info("[TASK] Result validated successfully")
        # Return result
        return result
    except Exception as e:
        logger.error(f"[TASK] Error in story generation for story_id={story_id}: {str(e)}", exc_info=True)
        logger.debug(f"[TASK] Error type: {type(e)}")
        raise e
