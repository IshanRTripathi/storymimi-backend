import io
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from app.database.supabase_client.base_db_client import SupabaseBaseClient
import logging
import time
import asyncio

logger = logging.getLogger(__name__)

class StorageService(SupabaseBaseClient):
    """Service for Supabase Storage operations"""
    
    def __init__(self):
        """Initialize storage service with proper client"""
        super().__init__()
        logger.info("Storage service initialized")
    
    def _ensure_bucket_exists(self, bucket_name: str, public: bool = True) -> None:
        """Ensure a storage bucket exists, creating it if necessary
        
        Args:
            bucket_name: The name of the bucket
            public: Whether the bucket should be public
            
        Raises:
            Exception: If bucket creation fails
        """
        logger.debug(f"Ensuring bucket exists: {bucket_name}")
        
        try:
            # Create bucket with public access
            self.storage.create_bucket(bucket_name)
            logger.info(f"Bucket created or already exists: {bucket_name}")
        except Exception as e:
            logger.warning(f"Failed to create bucket: {str(e)}")
            # Check if bucket exists by listing files
            try:
                files = self.storage.from_(bucket_name).list()
                if files:
                    logger.debug(f"Bucket already exists: {bucket_name}")
                    return
            except Exception as list_error:
                logger.warning(f"Failed to list files in bucket: {str(list_error)}")
                raise e from None

    async def upload_image(self, story_id: str, scene_index: int, image_bytes: bytes) -> str:
        """Upload an image to Supabase Storage and return the public URL
        
        Args:
            story_id: ID of the story
            scene_index: Index of the scene
            image_bytes: Bytes of the image to upload
            
        Returns:
            str: Public URL of the uploaded image
            
        Raises:
            Exception: If upload fails
        """
        logger.info(f"Uploading image for story: {story_id}, scene: {scene_index}")
        start_time = time.time()
        
        # Create a unique filename
        filename = f"scene_{scene_index}_{uuid.uuid4()}.png"
        bucket_name = "story-images"
        
        try:
            # Ensure bucket exists
            await self._ensure_bucket_exists(bucket_name)
            
            # Upload the image with proper content type using run_in_executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,  # Use default executor
                lambda: self.storage.from_(bucket_name).upload(
                    file=image_bytes,
                    path=filename,
                    file_options={"content-type": "image/png"}
                )
            )
            
            # Get the public URL
            public_url = f"https://{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
            logger.info(f"Image uploaded successfully in {time.time() - start_time:.2f}s: {public_url}")
            return public_url
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to upload image in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def upload_image(self, story_id: Union[str, uuid.UUID], scene_sequence: int, image_bytes: bytes) -> str:
        """Upload an image to Supabase Storage and return the public URL
        
        Args:
            story_id: The ID of the story
            scene_sequence: The sequence number of the scene
            image_bytes: The image data as bytes
            
        Returns:
            The public URL of the uploaded image
            
        Raises:
            Exception: If image upload fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        bucket_name = "story-images"
        file_path = f"{story_id_str}/{scene_sequence}.png"
        
        logger.info(f"Uploading image for story: {story_id_str}, scene: {scene_sequence}")
        
        try:
            # Ensure the bucket exists
            await self._ensure_bucket_exists(bucket_name)
            
            # Check if image data is valid
            if not image_bytes or len(image_bytes) < 100:
                logger.error(f"Invalid image data: too small or empty ({len(image_bytes) if image_bytes else 0} bytes)")
                raise ValueError("Invalid image data: too small or empty")
            
            # Upload the image
            logger.debug(f"Uploading image to {bucket_name}/{file_path}")
            
            # Convert bytes to BytesIO and use it directly
            image_io = io.BytesIO(image_bytes)
            image_io.seek(0)
            
            try:
                # Use the upload method with file content
                await self.storage.from_(bucket_name).upload(
                    file_path,
                    image_io.getvalue(),  # Use getvalue() to get bytes
                    file_options={"content-type": "image/png"}
                )
            except Exception as upload_error:
                logger.error(f"Error uploading image: {str(upload_error)}")
                raise
            finally:
                # Clean up the BytesIO object
                image_io.close()
            
            # Get the public URL
            public_url = await self.storage.from_(bucket_name).get_public_url(file_path)
            
            elapsed = time.time() - start_time
            logger.info(f"Image uploaded successfully in {elapsed:.2f}s: {public_url}")
            return public_url
        except Exception as e:
            elapsed = time.time() - start_time
            raise
        finally:
            # Log the end of the operation
            self._log_operation("upload", "images")
    
    async def upload_audio(self, story_id: Union[str, uuid], scene_sequence: int, audio_bytes: bytes) -> str:
        """Upload an audio file to Supabase Storage and return the public URL
        
        Args:
            story_id: The ID of the story
            scene_sequence: The sequence number of the scene
            audio_bytes: The audio data as bytes
            
        Returns:
            The public URL of the uploaded audio
            
        Raises:
            Exception: If audio upload fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        bucket_name = "story-audio"
        file_path = f"{story_id_str}/scene_{scene_sequence}.mp3"
        
        try:
            # Create BytesIO object and ensure it's reset to start
            audio_io = io.BytesIO(audio_bytes)
            audio_io.seek(0)
            
            # Upload using the utility method
            return await self._upload_file(bucket_name, file_path, audio_io.getvalue(), "audio/mpeg")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to upload audio in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
        finally:
            # Clean up the BytesIO object
            if hasattr(audio_io, 'close'):
                audio_io.close()
    
    async def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Delete a file from Supabase Storage
        
        Args:
            bucket_name: The name of the bucket
            file_path: The path to the file within the bucket
            
        Returns:
            True if deletion was successful, False otherwise
            
        Raises:
            Exception: If file deletion fails
        """
        start_time = time.time()
        
        logger.info(f"Deleting file from {bucket_name}: {file_path}")
        
        try:
            # Check if the bucket exists
            try:
                self.storage.get_bucket(bucket_name)
            except Exception:
                logger.warning(f"Bucket does not exist: {bucket_name}")
                return False
                
            # Delete the file
            self.storage.from_(bucket_name).remove([file_path])
            
            elapsed = time.time() - start_time
            logger.info(f"File deleted successfully in {elapsed:.2f}s: {bucket_name}/{file_path}")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete file in {elapsed:.2f}s: {str(e)}", exc_info=True)
            return False
    
    async def delete_story_files(self, story_id: Union[str, uuid]) -> Tuple[int, int]:
        """Delete all files associated with a story
        
        Args:
            story_id: The ID of the story
            
        Returns:
            Tuple of (images_deleted, audio_files_deleted)
            
        Raises:
            Exception: If file deletion fails
        """
        start_time = time.time()
        story_id_str = str(story_id)
        
        logger.info(f"Deleting all files for story: {story_id_str}")
        
        try:
            # Get list of scenes to know what files to delete
            scenes = await self.get_story_scenes(story_id_str)
            
            images_deleted = 0
            audio_deleted = 0
            
            # Delete image files
            for scene in scenes:
                sequence = scene["sequence"]
                
                # Delete image
                image_path = f"{story_id_str}/{sequence}.png"
                if await self.delete_file("story-images", image_path):
                    images_deleted += 1
                    
                # Delete audio
                audio_path = f"{story_id_str}/{sequence}.mp3"
                if await self.delete_file("story-audio", audio_path):
                    audio_deleted += 1
            
            elapsed = time.time() - start_time
            logger.info(f"Deleted {images_deleted} images and {audio_deleted} audio files in {elapsed:.2f}s for story: {story_id_str}")
            return (images_deleted, audio_deleted)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to delete story files in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
    
    async def list_bucket_files(self, bucket_name: str, path: str = "") -> List[Dict[str, Any]]:
        """List files in a bucket, optionally filtered by path prefix
        
        Args:
            bucket_name: The name of the bucket
            path: Optional path prefix to filter by
            
        Returns:
            List of file information dictionaries
            
        Raises:
            Exception: If listing files fails
        """
        start_time = time.time()
        
        logger.info(f"Listing files in bucket: {bucket_name}, path: {path}")
        
        try:
            # Check if the bucket exists
            try:
                self.storage.get_bucket(bucket_name)
            except Exception:
                logger.warning(f"Bucket does not exist: {bucket_name}")
                return []
                
            # List files
            response = self.storage.from_(bucket_name).list(path)
            files = response if response else []
            
            elapsed = time.time() - start_time
            logger.info(f"Listed {len(files)} files in {elapsed:.2f}s from bucket: {bucket_name}")
            return files
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to list files in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise
