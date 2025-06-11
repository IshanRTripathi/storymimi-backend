import io
import uuid
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from supabase import create_client, Client

from app.config import settings
from app.models.story import StoryStatus, Scene, StoryDetail
from app.models.user import User, UserResponse

class SupabaseClient:
    """Client for interacting with Supabase database and storage"""
    
    def __init__(self):
        """Initialize the Supabase client"""
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.storage = self.client.storage
    
    # User methods
    async def create_user(self, email: str, username: str) -> Dict[str, Any]:
        """Create a new user in the database"""
        user_data = {
            "email": email,
            "username": username,
            "user_id": str(uuid.uuid4())
        }
        
        response = self.client.table("users").insert(user_data).execute()
        return response.data[0] if response.data else None
    
    async def get_user(self, user_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        response = self.client.table("users").select("*").eq("user_id", str(user_id)).execute()
        return response.data[0] if response.data else None
    
    # Story methods
    async def create_story(self, title: str, prompt: str, user_id: Optional[Union[str, UUID]] = None) -> Dict[str, Any]:
        """Create a new story record with PENDING status"""
        story_id = uuid.uuid4()
        story_data = {
            "story_id": str(story_id),
            "title": title,
            "prompt": prompt,
            "status": StoryStatus.PENDING.value,
            "user_id": str(user_id) if user_id else None
        }
        
        response = self.client.table("stories").insert(story_data).execute()
        return response.data[0] if response.data else None
    
    async def get_story(self, story_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get a story by ID"""
        response = self.client.table("stories").select("*").eq("story_id", str(story_id)).execute()
        return response.data[0] if response.data else None
    
    async def update_story_status(self, story_id: Union[str, UUID], status: StoryStatus) -> bool:
        """Update the status of a story"""
        response = self.client.table("stories").update({"status": status.value}).eq("story_id", str(story_id)).execute()
        return bool(response.data)
    
    async def create_scene(self, story_id: Union[str, UUID], sequence: int, text: str, 
                          image_url: Optional[str] = None, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a new scene for a story"""
        scene_data = {
            "scene_id": str(uuid.uuid4()),
            "story_id": str(story_id),
            "sequence": sequence,
            "text": text,
            "image_url": image_url,
            "audio_url": audio_url
        }
        
        response = self.client.table("scenes").insert(scene_data).execute()
        return response.data[0] if response.data else None
    
    async def get_story_scenes(self, story_id: Union[str, UUID]) -> List[Dict[str, Any]]:
        """Get all scenes for a story, ordered by sequence"""
        response = self.client.table("scenes").select("*").eq("story_id", str(story_id)).order("sequence").execute()
        return response.data if response.data else []
    
    # Storage methods
    async def upload_image(self, story_id: Union[str, UUID], scene_sequence: int, image_bytes: bytes) -> str:
        """Upload an image to Supabase Storage and return the public URL"""
        bucket_name = "story-images"
        file_path = f"{story_id}/{scene_sequence}.png"
        
        # Ensure the bucket exists
        try:
            self.storage.get_bucket(bucket_name)
        except Exception:
            self.storage.create_bucket(bucket_name)
        
        # Upload the image
        self.storage.from_(bucket_name).upload(
            file_path,
            io.BytesIO(image_bytes),
            file_options={"content-type": "image/png"}
        )
        
        # Get the public URL
        public_url = self.storage.from_(bucket_name).get_public_url(file_path)
        return public_url
    
    async def upload_audio(self, story_id: Union[str, UUID], scene_sequence: int, audio_bytes: bytes) -> str:
        """Upload an audio file to Supabase Storage and return the public URL"""
        bucket_name = "story-audio"
        file_path = f"{story_id}/{scene_sequence}.mp3"
        
        # Ensure the bucket exists
        try:
            self.storage.get_bucket(bucket_name)
        except Exception:
            self.storage.create_bucket(bucket_name)
        
        # Upload the audio
        self.storage.from_(bucket_name).upload(
            file_path,
            io.BytesIO(audio_bytes),
            file_options={"content-type": "audio/mpeg"}
        )
        
        # Get the public URL
        public_url = self.storage.from_(bucket_name).get_public_url(file_path)
        return public_url