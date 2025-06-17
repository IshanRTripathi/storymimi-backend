import io
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path

from app.database.supabase_client.base_db_client import SupabaseBaseClient
import logging
import time
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Base exception for storage-related errors"""
    pass

class StorageApiError(StorageError):
    """Exception for storage API errors"""
    pass

class StorageService(SupabaseBaseClient):
    """Service for handling file storage operations in Supabase"""
    
    DEFAULT_CACHE_CONTROL = "max-age=31536000"  # 1 year
    AUDIO_BUCKET = "audio"
    IMAGE_BUCKET = "images"
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize the storage service with Supabase credentials."""
        from app.config import settings
        self.supabase_url = supabase_url or settings.SUPABASE_URL
        self.supabase_key = supabase_key or settings.SUPABASE_KEY
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.max_retries = 3
        self.timeout = 100
        super().__init__()
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 3600  # Cache TTL in seconds
        self._last_cleanup = time.time()
        
    def _get_cache_key(self, bucket: str, file_path: str) -> str:
        """Generate a cache key for a file"""
        return f"{bucket}:{file_path}"
        
    def _get_from_cache(self, bucket: str, file_path: str) -> Optional[str]:
        """Get a URL from cache if it exists and is not expired"""
        key = self._get_cache_key(bucket, file_path)
        if key in self._cache:
            url, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return url
            else:
                logger.debug(f"Cache expired for {key}")
                del self._cache[key]
        return None
        
    def _add_to_cache(self, bucket: str, file_path: str, url: str):
        """Add a URL to cache"""
        key = self._get_cache_key(bucket, file_path)
        self._cache[key] = (url, time.time())
        logger.debug(f"Added to cache: {key}")
        
        # Cleanup old cache entries periodically
        if time.time() - self._last_cleanup > 3600:  # Cleanup every hour
            self._cleanup_cache()
            
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if now - timestamp > self._cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        self._last_cleanup = now
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

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

    async def upload_image(self, story_id: str, scene_num: int, image_bytes: bytes) -> str:
        """Upload an image to Supabase Storage and return its public URL."""
        file_path = f"{story_id}/scene_{scene_num}.png"
        backoff = 1
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[📤 Upload Attempt {attempt}] Uploading image for scene {scene_num}...")
                self.client.storage.from_(self.IMAGE_BUCKET).upload(
                    file_path,
                    image_bytes,
                    {"content-type": "image/png"}
                )
                public_url = self.client.storage.from_(self.IMAGE_BUCKET).get_public_url(file_path)
                logger.info(f"[✅ Upload success] Image uploaded for scene {scene_num}")
                return public_url
            except Exception as e:
                logger.warning(f"[Upload Retry {attempt}] {e}, retrying in {backoff}s...")
                if attempt == self.max_retries:
                    logger.error(f"[Upload Failed] Failed after {self.max_retries} retries: {str(e)}")
                    raise RuntimeError(f"Image upload failed after {self.max_retries} retries: {str(e)}")
                time.sleep(backoff)
                backoff *= 2

    async def upload_audio(self, story_id: str, scene_num: int, audio_bytes: bytes) -> str:
        """Upload an audio file to Supabase Storage and return its public URL."""
        file_path = f"{story_id}/scene_{scene_num}.mp3"
        backoff = 1
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[📤 Upload Attempt {attempt}] Uploading audio for scene {scene_num}...")
                self.client.storage.from_(self.AUDIO_BUCKET).upload(
                    file_path,
                    audio_bytes,
                    {"content-type": "audio/mpeg"}
                )
                public_url = self.client.storage.from_(self.AUDIO_BUCKET).get_public_url(file_path)
                logger.info(f"[✅ Upload success] Audio uploaded for scene {scene_num}")
                return public_url
            except Exception as e:
                logger.warning(f"[Upload Retry {attempt}] {e}, retrying in {backoff}s...")
                if attempt == self.max_retries:
                    logger.error(f"[Upload Failed] Failed after {self.max_retries} retries: {str(e)}")
                    raise RuntimeError(f"Audio upload failed after {self.max_retries} retries: {str(e)}")
                time.sleep(backoff)
                backoff *= 2
    
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
