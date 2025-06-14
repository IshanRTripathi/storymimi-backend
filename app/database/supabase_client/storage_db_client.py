import io
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path

from app.database.supabase_client.base_db_client import SupabaseBaseClient
import logging
import time

logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Base exception for storage-related errors"""
    pass

class StorageApiError(StorageError):
    """Exception for storage API errors"""
    pass

class StorageService(SupabaseBaseClient):
    """Service for Supabase Storage operations"""
    
    DEFAULT_CACHE_CONTROL = "max-age=31536000"  # 1 year
    AUDIO_BUCKET = "audio"
    IMAGE_BUCKET = "images"
    
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
            StorageError: If bucket creation fails
        """
        logger.debug(f"Ensuring bucket exists: {bucket_name}")
        
        try:
            # Check if bucket exists
            buckets = self.storage.list_buckets()
            existing_bucket = next((b for b in buckets if b.id == bucket_name), None)
            
            if existing_bucket:
                logger.info(f"Bucket {bucket_name} already exists")
                return
                
            # Set bucket options based on type
            if bucket_name == self.IMAGE_BUCKET:
                options = {
                    "public": True,
                    "file_size_limit": 52428800,  # 50MB
                    "allowed_mime_types": ["image/*"]
                }
            else:  # AUDIO_BUCKET
                options = {
                    "public": True,
                    "file_size_limit": 52428800,  # 50MB
                    "allowed_mime_types": ["audio/*"]
                }
            
            try:
                self.storage.create_bucket(bucket_name, options=options)
                logger.info(f"Bucket created: {bucket_name}")
            except Exception as e:
                logger.error(f"Failed to create bucket {bucket_name}: {str(e)}")
                raise StorageError(f"Failed to create bucket {bucket_name}") from e
            logger.info(f"Bucket created: {bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to ensure bucket {bucket_name} exists: {str(e)}")
            raise StorageError(f"Failed to ensure bucket {bucket_name} exists") from e

    def upload_image(self, story_id: str, scene_index: int, image_bytes: bytes) -> str:
        """Upload an image to Supabase Storage and return the public URL
        
        Args:
            story_id: The ID of the story
            scene_index: The index of the scene
            image_bytes: The image bytes to upload
            
        Returns:
            str: The public URL of the uploaded image
            
        Raises:
            StorageError: If the upload fails
        """
        try:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"story_{story_id}_scene_{scene_index}_{timestamp}.png"
            
            # Upload file
            file_path = f"stories/{story_id}/{filename}"
            self._ensure_bucket_exists(self.IMAGE_BUCKET)
            
            # Ensure image_bytes is in bytes format
            if isinstance(image_bytes, str):
                image_bytes = image_bytes.encode()
            
            # Upload the file
            result = self.storage.from_(self.IMAGE_BUCKET).upload(
                file_path,
                image_bytes,
                {
                    'Content-Type': 'image/png',
                    'Cache-Control': self.DEFAULT_CACHE_CONTROL
                }
            )
            
            # Get public URL
            url = self.storage.from_(self.IMAGE_BUCKET).get_public_url(file_path)
            logger.info(f"Image uploaded successfully: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to upload image: {str(e)}")
            raise StorageError(f"Failed to upload image: {str(e)}") from e
    
    def upload_audio(self, story_id: str, scene_index: int, audio_bytes: bytes) -> str:
        """
        Upload an audio file to Supabase Storage and return the public URL
        
        Args:
            story_id: The ID of the story
            scene_index: The index of the scene
            audio_bytes: The audio data as bytes
            
        Returns:
            str: The public URL of the uploaded audio
            
        Raises:
            StorageError: If upload fails
        """
        start_time = time.time()
        try:
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"story_{story_id}_scene_{scene_index}_{timestamp}.mp3"
            
            # Upload file
            # Use forward slashes for Supabase paths
            file_path = f"audio/{story_id}/{filename}"
            self._ensure_bucket_exists(self.AUDIO_BUCKET)
            
            # Upload the file
            result = self.storage.from_(self.AUDIO_BUCKET).upload(
                file_path,
                audio_bytes,
                {
                    'Content-Type': 'audio/mpeg',
                    'Cache-Control': self.DEFAULT_CACHE_CONTROL
                }
            )
            
            if not result:
                raise StorageError("Upload failed: No result returned")
                
            # Get public URL
            url = self.storage.from_(self.AUDIO_BUCKET).get_public_url(str(file_path))
            
            logger.info(f"Audio uploaded successfully: {url}")
            return url
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to upload audio in {elapsed:.2f}s: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to upload audio: {str(e)}") from e
    
    def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """Delete a file from Supabase Storage
        
        Args:
            bucket_name: The name of the bucket
            file_path: The path to the file
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            result = self.storage.from_(bucket_name).remove([file_path])
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete file {file_path} from bucket {bucket_name}: {str(e)}")
            raise StorageError(f"Failed to delete file: {str(e)}") from e
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
