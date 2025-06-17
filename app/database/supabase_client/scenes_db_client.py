from typing import Dict, Optional, Any, Union, List
from uuid import UUID
from datetime import datetime
from app.models.story_types import Scene
from app.database.supabase_client.base_db_client import SupabaseBaseClient
import logging
import time
import uuid

logger = logging.getLogger(__name__)

class SceneRepository(SupabaseBaseClient):
    """Repository for scene-related operations"""
    
    async def create_scene(self, scene: Scene, user_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """Create a new scene for a story with audit trail
        
        Args:
            story_id: The ID of the story
            sequence: The sequence number of the scene
            title: The title of the scene
            text: The text content of the scene
            image_prompt: The prompt used to generate the scene image
            image_url: URL to the scene's image
            audio_url: URL to the scene's audio
            user_id: Optional ID of user creating the scene
            
        Returns:
            The created scene data or None if creation failed
            
        Raises:
            Exception: If scene creation fails
        """
        start_time = time.time()
        scene_id_str = str(scene.scene_id)
        story_id_str = str(scene.story_id)
        user_id_str = str(user_id) if user_id else None
        
        # Create scene data with timestamps
        now = datetime.now().isoformat()
        scene_data = {
            "scene_id": scene_id_str,
            "story_id": story_id_str,
            "sequence": scene.sequence,
            "title": scene.title,
            "text": scene.text,
            "image_prompt": scene.image_prompt,
            "image_url": scene.image_url,
            "audio_url": scene.audio_url,
            "created_at": now,
            "updated_at": now
        }
        
        if user_id:
            scene_data["user_id"] = user_id_str
            
        self._log_operation("insert", "scenes", scene_data)
        logger.info(f"Creating scene with ID: {scene_id_str}")
        
        try:
            response = self.client.table("scenes").insert(scene_data).execute()
            
            if not response.data:
                logger.error(f"Failed to create scene: No data returned from database")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Scene created successfully in {elapsed:.2f}s: {scene_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to create scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_scene(self, scene_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a scene by ID
        
        Args:
            scene_id: The ID of the scene to retrieve
            
        Returns:
            The scene data or None if not found
            
        Raises:
            Exception: If scene retrieval fails
        """
        start_time = time.time()
        scene_id_str = str(scene_id)
        
        self._log_operation("select", "scenes", filters={"scene_id": scene_id_str})
        logger.info(f"Getting scene with ID: {scene_id_str}")
        
        try:
            response = self.client.table("scenes").select("*").eq("scene_id", scene_id_str).execute()
            
            if not response.data:
                logger.warning(f"Scene not found with ID: {scene_id_str}")
                return None
                
            elapsed = time.time() - start_time
            logger.info(f"Scene retrieved successfully in {elapsed:.2f}s: {scene_id_str}")
            return response.data[0]
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def get_story_scenes(self, story_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """Get all scenes for a story, ordered by sequence
        
        Args:
            story_id: The ID of the story to get scenes for
            
        Returns:
            List of scene data dictionaries
            
        Raises:
            Exception: If scene retrieval fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        self._log_operation("select", "scenes", filters={"story_id": story_id_str})
        logger.info(f"Getting scenes for story ID: {story_id_str}")
        
        try:
            response = self.client.table("scenes").select("*").eq("story_id", story_id_str).order("sequence").execute()
            scenes = response.data if response.data else []
            
            elapsed = time.time() - start_time
            logger.info(f"Retrieved {len(scenes)} scenes successfully in {elapsed:.2f}s for story: {story_id_str}")
            return scenes
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to get scenes in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def delete_scene(self, scene_id: Union[str, UUID]) -> bool:
        """Delete a scene
        
        Args:
            scene_id: The ID of the scene to delete
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If scene deletion fails
        """
        start_time = time.time()
        scene_id_str = str(scene_id)
        
        self._log_operation("delete", "scenes", filters={"scene_id": scene_id_str})
        logger.info(f"Deleting scene with ID: {scene_id_str}")
        
        try:
            response = self.client.table("scenes").delete().eq("scene_id", scene_id_str).execute()
            success = bool(response.data)
            
            elapsed = time.time() - start_time
            if success:
                logger.info(f"Scene deleted successfully in {elapsed:.2f}s: {scene_id_str}")
            else:
                logger.warning(f"Scene deletion returned no data in {elapsed:.2f}s: {scene_id_str}")
                
            return success
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete scene in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def batch_insert_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert multiple scenes in a single operation
        
        Args:
            scenes: List of scene data dictionaries
            
        Returns:
            List of created scene data
            
        Raises:
            Exception: If batch insert fails
        """
        start_time = time.time()
        
        if not scenes:
            logger.warning("No scenes provided for batch insert")
            return []
        
        # Ensure all scenes have scene_id
        for scene in scenes:
            if "scene_id" not in scene:
                scene["scene_id"] = str(uuid.uuid4())
        
        self._log_operation("insert", "scenes", scenes)
        logger.info(f"Batch inserting {len(scenes)} scenes")
        
        try:
            response = self.client.table("scenes").insert(scenes).execute()
            created_scenes = response.data if response.data else []
            
            elapsed = time.time() - start_time
            logger.info(f"Successfully inserted {len(created_scenes)} scenes in {elapsed:.2f}s")
            return created_scenes
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to batch insert scenes in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
        finally:
            self._log_operation("insert", "scenes", result=len(created_scenes))
