import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from app.database.supabase_client import StoryRepository, SceneRepository, StorageService, UserRepository
from app.models.story_types import StoryStatus, StoryRequest, StoryResponse, Scene, StoryDetail
from app.services.ai_service import AIService
from app.services.story_extractor import StoryExtractor
from app.services.story_processor import StoryProcessor
from app.services.story_prompt_service import StoryPromptService
from app.utils.json_converter import JSONConverter
from app.utils.validator import Validator

logger = logging.getLogger(__name__)


class StoryGenerator:
    """Service for generating stories asynchronously"""
    
    def __init__(self, 
                 story_client: StoryRepository,
                 scene_client: SceneRepository,
                 storage_service: StorageService,
                 story_prompt_service: StoryPromptService,
                 user_client: UserRepository):
        self.story_client = story_client
        self.scene_client = scene_client
        self.storage_service = storage_service
        self.story_prompt_service = story_prompt_service
        self.user_client = user_client

    async def generate_story(self, story_id: str, request: StoryRequest, user_id: str) -> Dict[str, Any]:
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
            logger.info(f"[GENERATOR] Starting generation for story_id={story_id}")

            # 1. Get existing story data (it should exist from create_new_story)
            story_data = await self.story_client.get_story(story_id)
            if not story_data:
                raise ValueError(f"Story not found: {story_id}")
            logger.debug(f"[GENERATOR] Retrieved story data: {story_data}")

            # 2. Call LLM to generate structured story metadata
            # (This replaces the initial generate_story call to AIService)
            structured_story_metadata = await self.story_prompt_service.generate_structured_story(request.prompt)
            logger.info(f"[GENERATOR] Structured story metadata generated for story_id={story_id}")
            logger.debug(f"[GENERATOR] Generated story metadata: {structured_story_metadata}")

            # 3. Update the story in DB with story_metadata (write-once)
            await self.story_client.update_story(story_id, {"story_metadata": structured_story_metadata}, user_id=user_id)
            logger.info(f"[GENERATOR] Story metadata saved for story_id={story_id}")

            # Extract data from structured_story_metadata for further steps
            story_metadata = structured_story_metadata.get("story_metadata", {})
            scenes_data = story_metadata.get("scenes", [])
            
            # 4. Update story status to PROCESSING
            await self.story_client.update_story_status(story_id, StoryStatus.PROCESSING, user_id=user_id)
            logger.info(f"[GENERATOR] Story status updated to PROCESSING for story_id={story_id}")

            # 5. Generate visual profile and base style (once per story)
            visual_profile = await self.story_prompt_service.generate_visual_profile(story_metadata)
            base_style = await self.story_prompt_service.generate_base_style(story_metadata)
            logger.info(f"[GENERATOR] Generated visual profile and base style for story_id={story_id}")

            # 6. Generate scenes in parallel
            generated_scenes = []
            for i, scene_data in enumerate(scenes_data):
                current_scene = Scene(
                    scene_id=str(uuid4()),
                    story_id=story_id,
                    sequence=i,
                    title=scene_data.get("title", f"Scene {i + 1}"),
                    description=scene_data.get("description", ""),
                    prompt=scene_data.get("prompt", ""),
                    image_prompt=scene_data.get("image_prompt", ""),
                    audio_prompt=scene_data.get("audio_prompt", ""),
                    status=StoryStatus.PROCESSING,
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat()
                )
                generated_scenes.append(current_scene)
                
                await process_single_scene(self.scene_client, self.storage_service, ai_service, story_id, i, current_scene, self.story_client)
        
            # Complete story with all generated scenes and updated data
            return await complete_story(self.story_client, story_data, generated_scenes)

        except Exception as e:
            logger.exception(f"[GENERATOR] Error occurred for story_id={story_id}")
            return await handle_story_error(self.story_client, story_id, e)

async def process_single_scene(scene_client: SceneRepository, storage_service: StorageService, 
                               ai_service: AIService, story_id: str, index: int, scene: Scene):
    """Process a single scene including media generation and database storage."""
    logger.info(f"[GENERATOR] Processing scene {index+1}")
    
    # Generate and store media first
    try:
        # Generate image
        image_url = await ai_service.generate_image(scene.image_prompt)
        if image_url:
            scene.image_url = image_url
            await storage_service.upload_image(story_id, index, image_url)
            logger.info(f"[GENERATOR] Image generated and stored for scene {index + 1}")
        
        # Generate audio
        audio_url = await ai_service.generate_audio(scene.audio_prompt)
        if audio_url:
            scene.audio_url = audio_url
            await storage_service.upload_audio(story_id, index, audio_url)
            logger.info(f"[GENERATOR] Audio generated and stored for scene {index + 1}")
    except Exception as e:
        logger.error(f"[GENERATOR] Failed to generate media for scene {index + 1}: {str(e)}", exc_info=True)
        raise
    
    # Create and update scene in database with media URLs
    await scene_client.create_scene(scene)
    logger.info(f"[GENERATOR] Scene {index+1} created successfully in DB with media URLs")

# Remove this function as it's redundant with process_single_scene
# The media generation is already handled in process_single_scene
# This function can be removed since it's not being used

async def complete_story(story_client: StoryRepository, story_data: Dict[str, Any], scenes: List[Scene]) -> Dict[str, Any]:
    """Complete story generation and return final response."""
    logger.info(f"[GENERATOR] Completing story for story_id={story_data['story_id']}")
    
    # Update story status to completed
    await story_client.update_story_status(story_data["story_id"], StoryStatus.COMPLETED)
    
    # Convert scenes to dictionaries before returning
    scene_dicts = []
    for scene in scenes:
        scene_dict = {
            "scene_id": str(scene.scene_id),
            "story_id": str(scene.story_id),
            "sequence": scene.sequence,
            "title": scene.title,
            "text": scene.text,
            "image_prompt": scene.image_prompt,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "created_at": scene.created_at,
            "updated_at": scene.updated_at
        }
        scene_dicts.append(scene_dict)
    
    # Ensure story_metadata is always a dictionary
    story_metadata = story_data.get("story_metadata")
    if story_metadata is None:
        story_metadata = {}
    elif not isinstance(story_metadata, dict):
        logger.warning(f"[GENERATOR] story_metadata is not a dict, converting to empty dict. Type: {type(story_metadata)}")
        story_metadata = {}
    
    return {
        "story_id": story_data["story_id"],
        "title": story_data["title"],
        "status": StoryStatus.COMPLETED,
        "scenes": scene_dicts,
        "user_id": story_data["user_id"],
        "cover_image_url": story_data.get("cover_image_url"),
        "created_at": story_data["created_at"],
        "updated_at": story_data["updated_at"],
        "story_metadata": story_metadata
    }

async def handle_story_error(story_client: StoryRepository, story_id: str, error: Exception) -> Dict[str, Any]:
    """Handle story generation error and return error response."""
    await story_client.update_story_status(story_id, StoryStatus.FAILED)
    
    # Get the actual story data from the database
    story_data = await story_client.get_story(story_id)
    
    # Ensure story_metadata is always a dictionary
    story_metadata = story_data.get("story_metadata")
    if story_metadata is None:
        story_metadata = {}
    elif not isinstance(story_metadata, dict):
        logger.warning(f"[GENERATOR] story_metadata is not a dict in error handler, converting to empty dict. Type: {type(story_metadata)}")
        story_metadata = {}
    
    return {
        "story_id": story_data["story_id"],
        "title": story_data["title"],
        "status": StoryStatus.FAILED,
        "scenes": [],
        "user_id": story_data["user_id"],
        "cover_image_url": story_data.get("cover_image_url"),
        "created_at": story_data.get("created_at"),
        "updated_at": story_data.get("updated_at"),
        "story_metadata": story_metadata,
        "error": str(error)
    }

    try:
        logger.info(f"[GENERATOR] Starting generation for story_id={story_id}")

        # 1. Get existing story data (it should exist from create_new_story)
        story_data = await story_client.get_story(story_id)
        if not story_data:
            raise ValueError(f"Story not found: {story_id}")
        logger.debug(f"[GENERATOR] Retrieved story data: {story_data}")

        # 2. Call LLM to generate structured story metadata
        # (This replaces the initial generate_story call to AIService)
        structured_story_metadata = await story_prompt_service.generate_structured_story(request.prompt)
        logger.info(f"[GENERATOR] Structured story metadata generated for story_id={story_id}")
        logger.debug(f"[GENERATOR] Generated story metadata: {structured_story_metadata}")

        # 3. Update the story in DB with story_metadata (write-once)
        await self.story_client.update_story(story_id, {"story_metadata": structured_story_metadata}, user_id=user_id)
        logger.info(f"[GENERATOR] Story metadata saved for story_id={story_id}")

        # Extract data from structured_story_metadata for further steps
        child_profile = structured_story_metadata.get("child_profile", {})
        side_character = structured_story_metadata.get("side_character", {})
        story_meta = structured_story_metadata.get("story_meta", {})
        scenes_from_llm = structured_story_metadata.get("scenes", [])

        # Update initial story_data with new title from structured_story_metadata
        # and ensure other fields are consistent.
        story_data["title"] = story_meta.get("story_title", story_data.get("title", "Untitled"))
        story_data["prompt"] = request.prompt # Ensure original prompt is retained if needed
        story_data["story_metadata"] = structured_story_metadata # For internal use later if needed
        logger.debug(f"[GENERATOR] Updated story data with metadata: {story_data}")

        # 4. Update story status to PROCESSING
        await self.story_client.update_story_status(story_id, StoryStatus.PROCESSING, user_id=user_id)
        logger.info(f"[GENERATOR] Story status updated to PROCESSING for story_id={story_id}")

        # 5. Generate visual profile and base style (once per story)
        visual_profile = await story_prompt_service.generate_visual_profile(child_profile, side_character)
        base_style = await story_prompt_service.generate_base_style(
            story_meta.get("setting_description", ""),
            story_meta.get("tone", "warm and whimsical")
        )
        logger.info(f"[GENERATOR] Visual profile and base style generated for story_id={story_id}")

        # Prepare scene objects based on LLM output and add generated media URLs
        generated_scenes: List[Scene] = []

        # Assuming AIService still handles image and audio generation directly
        async with AIService() as ai_service:
            for i, llm_scene in enumerate(scenes_from_llm):
                scene_text = llm_scene.get("text", "")
                scene_title = llm_scene.get("scene_number", i + 1) # Use scene_number as title, or sequence
                story_so_far = llm_scene.get("story_so_far", "")
                # Generate scene moment
                scene_moment_prompt = await story_prompt_service.generate_scene_moment(scene_text, story_so_far)

                # Compose full image prompt
                full_image_prompt = f"Base style: {base_style}. In {story_meta.get('setting_description', 'a magical setting')}, {child_profile.get('name', 'a child')}, {visual_profile.get('character_prompt', '')}, {scene_moment_prompt} {visual_profile.get('side_character_prompt', '')}".strip()

                current_scene = Scene(
                    scene_id=uuid4(),
                    story_id=UUID(story_id),
                    sequence=i + 1,  # 1-based sequence
                    title=f"Scene {scene_title}",
                    text=scene_text,
                    image_prompt=full_image_prompt, # Use the generated full prompt
                    image_url=None, # Will be filled after upload
                    audio_url=None, # Will be filled after upload
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                generated_scenes.append(current_scene)
                
                await process_single_scene(scene_client, storage_service, ai_service, story_id, i, current_scene, story_client)
        
        # Complete story with all generated scenes and updated data
        return await complete_story(story_client, story_data, generated_scenes)

    except Exception as e:
        logger.exception(f"[GENERATOR] Error occurred for story_id={story_id}")
        return await handle_story_error(story_client, story_id, e)

async def process_single_scene(scene_client: SceneRepository, storage_service: StorageService, 
                       ai_service: AIService, story_id: str, index: int, scene: Scene, story_client: StoryRepository = None):
    """Process a single scene including media generation and database storage."""
    logger.info(f"[GENERATOR] Processing scene {index+1}")
    
    # Generate and upload media (includes cover image update for first scene)
    await generate_and_store_media(storage_service, ai_service, story_id, index, scene, story_client)
    
    # Create and update scene in database
    # The scene object already contains all fields including image_prompt
    await scene_client.create_scene(scene)
    logger.info(f"[GENERATOR] Scene {index+1} created successfully in DB")

async def generate_and_store_media(storage_service: StorageService, ai_service: AIService, 
                                 story_id: str, index: int, scene: Scene, story_client: StoryRepository = None):
    """Generate and store media (image and audio) for a scene."""
    # Generate and upload image
    logger.debug(f"[GENERATOR] Generating and uploading image for scene {index+1}")
    try:
        image_bytes = await ai_service.generate_image(scene.image_prompt)
        image_url = await storage_service.upload_image(story_id, index, image_bytes)
        scene.image_url = image_url
        logger.debug(f"[GENERATOR] Image URL: {image_url}")
        
        # Update story cover image if this is the first scene (index 0) and story_client is provided
        if index == 0 and story_client and image_url:
            try:
                cover_updated = await story_client.update_story_cover_image_if_null(story_id, image_url)
                if cover_updated:
                    logger.info(f"[GENERATOR] Cover image set for story {story_id} from first scene")
                else:
                    logger.debug(f"[GENERATOR] Cover image already set for story {story_id}")
            except Exception as cover_error:
                logger.warning(f"[GENERATOR] Failed to update cover image for story {story_id}: {str(cover_error)}")
                # Don't raise here - cover image update is not critical for story generation
                
    except Exception as e:
        logger.error(f"[GENERATOR] Failed to process image: {str(e)}", exc_info=True)
        raise
    
    # Generate and upload audio
    logger.debug(f"[GENERATOR] Generating and uploading audio for scene {index+1}")
    try:
        audio_bytes = await ai_service.generate_audio(scene.text)
        audio_url = await storage_service.upload_audio(story_id, index, audio_bytes)
        scene.audio_url = audio_url
        logger.debug(f"[GENERATOR] Audio URL: {audio_url}")
    except Exception as e:
        logger.error(f"[GENERATOR] Failed to process audio: {str(e)}", exc_info=True)
        raise

async def complete_story(story_client: StoryRepository, story_data: Dict[str, Any], scenes: List[Scene]) -> Dict[str, Any]:
    """Complete story generation and return final response."""
    logger.info(f"[GENERATOR] Completing story for story_id={story_data['story_id']}")
    
    # Update story status to completed
    await story_client.update_story_status(story_data["story_id"], StoryStatus.COMPLETED)
    
    # Convert scenes to dictionaries before returning
    scene_dicts = []
    for scene in scenes:
        scene_dict = {
            "scene_id": str(scene.scene_id),
            "story_id": str(scene.story_id),
            "sequence": scene.sequence,
            "title": scene.title,
            "text": scene.text,
            "image_prompt": scene.image_prompt,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "created_at": scene.created_at,
            "updated_at": scene.updated_at
        }
        scene_dicts.append(scene_dict)
    
    # Ensure story_metadata is always a dictionary
    story_metadata = story_data.get("story_metadata")
    if story_metadata is None:
        story_metadata = {}
    elif not isinstance(story_metadata, dict):
        logger.warning(f"[GENERATOR] story_metadata is not a dict, converting to empty dict. Type: {type(story_metadata)}")
        story_metadata = {}
    
    return {
        "story_id": story_data["story_id"],
        "title": story_data["title"],
        "status": StoryStatus.COMPLETED,
        "scenes": scene_dicts,
        "user_id": story_data["user_id"],
        "cover_image_url": story_data.get("cover_image_url"),
        "created_at": story_data["created_at"],
        "updated_at": story_data["updated_at"],
        "story_metadata": story_metadata
    }

async def handle_story_error(story_client: StoryRepository, story_id: str, error: Exception) -> Dict[str, Any]:
    """Handle story generation error and return error response."""
    await story_client.update_story_status(story_id, StoryStatus.FAILED)
    
    # Get the actual story data from the database
    story_data = await story_client.get_story(story_id)
    
    # Ensure story_metadata is always a dictionary
    story_metadata = story_data.get("story_metadata")
    if story_metadata is None:
        story_metadata = {}
    elif not isinstance(story_metadata, dict):
        logger.warning(f"[GENERATOR] story_metadata is not a dict in error handler, converting to empty dict. Type: {type(story_metadata)}")
        story_metadata = {}
    
    return {
        "story_id": story_data["story_id"],
        "title": story_data["title"],
        "status": StoryStatus.FAILED,
        "scenes": [],
        "user_id": story_data["user_id"],
        "cover_image_url": story_data.get("cover_image_url"),
        "created_at": story_data.get("created_at"),
        "updated_at": story_data.get("updated_at"),
        "story_metadata": story_metadata,
        "error": str(error)
    }
