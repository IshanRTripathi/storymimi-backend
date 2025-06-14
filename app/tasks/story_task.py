import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from app.utils.validator import Validator
from app.utils.json_converter import JSONConverter
from app.core.celery_app import celery_app
from app.models.story_types import StoryRequest, StoryResponse, StoryStatus
from app.services.story_generator import generate_story_async
from app.database.supabase_client import StoryRepository

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="story_task.generate")
class StoryTask:
    """
    Celery task for generating stories with proper async handling and error management.
    
    This task handles:
    - Async story generation
    - File uploads
    - Error handling and logging
    - Progress tracking
    - Resource cleanup
    """
    
    def __init__(self):
        self.db_client = StoryRepository()
        self.loop = None

    def __del__(self):
        """Clean up resources when task is destroyed"""
        if self.loop and not self.loop.is_closed():
            self.loop.close()

    def run(self, story_id: str, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main task entry point.
        
        Args:
            story_id: ID of the story to generate
            request_dict: Dictionary containing story generation request
            
        Returns:
            Dictionary with the generated story data
            
        Raises:
            Exception: If story generation fails
        """
        try:
            # Update story status to processing
            self.db_client.update_story_status(story_id, StoryStatus.PROCESSING)
            
            # Create and set event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Parse request
            request = StoryRequest(**request_dict)
            logger.info(f"[TASK] Starting story generation for story_id={story_id}")
            logger.debug(f"[TASK] Request: {request}")
            
            # Run async story generation
            result = self.loop.run_until_complete(
                generate_story_async(story_id, request)
            )
            
            # Validate result
            Validator.validate_model_data(result, is_completion=True)
            
            # Convert to response
            response = JSONConverter.parse_json(result, StoryResponse)
            
            # Update story status to completed
            self.db_client.update_story_status(story_id, StoryStatus.COMPLETED)
            
            logger.info(f"[TASK] Story generation completed for story_id={story_id}")
            return response.dict()
            
        except Exception as e:
            logger.error(f"[TASK] Error generating story for story_id={story_id}: {str(e)}", exc_info=True)
            # Update story status to failed
            self.db_client.update_story_status(story_id, StoryStatus.FAILED)
            raise
        finally:
            # Clean up event loop
            if self.loop and not self.loop.is_closed():
                self.loop.close()
                self.loop = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        story_id = args[0]
        logger.error(f"[TASK] Task failed for story_id={story_id}: {str(exc)}")
        self.db_client.update_story_status(story_id, StoryStatus.FAILED)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        story_id = args[0]
        logger.warning(f"[TASK] Retrying task for story_id={story_id}: {str(exc)}")
        self.db_client.update_story_status(story_id, StoryStatus.RETRYING)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        story_id = args[0]
        logger.info(f"[TASK] Task succeeded for story_id={story_id}")
        self.db_client.update_story_status(story_id, StoryStatus.COMPLETED)
