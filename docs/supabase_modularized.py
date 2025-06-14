# base.py
import logging
from supabase import create_client
from app.config import settings

logger = logging.getLogger(__name__)

class SupabaseBaseClient:
    def __init__(self):
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            self.storage = self.client.storage
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error("Failed to initialize Supabase client", exc_info=True)
            raise

    def _log_operation(self, operation: str, table: str, data=None, filters=None):
        logger.debug({
            "operation": operation,
            "table": table,
            "data": data,
            "filters": filters,
        })


# users.py
from typing import Union, Optional, Dict, Any, List
from uuid import UUID
import time
import logging

from .base import SupabaseBaseClient

logger = logging.getLogger(__name__)

class UserRepository(SupabaseBaseClient):
    async def create_user(self, email: str, username: str) -> Optional[Dict[str, Any]]:
        user_data = {
            "email": email,
            "username": username,
            "user_id": str(uuid.uuid4()),
        }
        self._log_operation("insert", "users", user_data)
        try:
            response = self.client.table("users").insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception:
            logger.exception("Failed to create user")
            raise

    async def get_user(self, user_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        self._log_operation("select", "users", filters={"user_id": str(user_id)})
        try:
            response = self.client.table("users").select("*").eq("user_id", str(user_id)).execute()
            return response.data[0] if response.data else None
        except Exception:
            logger.exception("Failed to get user")
            raise

    # ... other user methods


# stories.py
from typing import Union, Optional, Dict, Any, List
from uuid import UUID
import uuid
import logging
from datetime import datetime

from .base import SupabaseBaseClient
from app.models.story_types import StoryStatus

logger = logging.getLogger(__name__)

class StoryRepository(SupabaseBaseClient):
    async def create_story(self, title: str, prompt: str, user_id: Optional[Union[str, UUID]] = None) -> Optional[Dict[str, Any]]:
        story_data = {
            "story_id": str(uuid.uuid4()),
            "title": title,
            "prompt": prompt,
            "status": StoryStatus.PENDING,
            "user_id": str(user_id) if user_id else None,
        }
        self._log_operation("insert", "stories", story_data)
        try:
            response = self.client.table("stories").insert(story_data).execute()
            return response.data[0] if response.data else None
        except Exception:
            logger.exception("Failed to create story")
            raise

    async def update_story_status(self, story_id: Union[str, UUID], status: StoryStatus) -> bool:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        try:
            response = self.client.table("stories").update(update_data).eq("story_id", str(story_id)).execute()
            return bool(response.data)
        except Exception:
            logger.exception("Failed to update story status")
            raise

    # ... other story methods


# scenes.py
from typing import Union, Optional, Dict, Any, List
from uuid import UUID
import uuid
import logging

from .base import SupabaseBaseClient

logger = logging.getLogger(__name__)

class SceneRepository(SupabaseBaseClient):
    async def create_scene(self, story_id: Union[str, UUID], sequence: int, text: str, image_url: str, audio_url: str) -> bool:
        scene_data = {
            "scene_id": str(uuid.uuid4()),
            "story_id": str(story_id),
            "sequence": sequence,
            "text": text,
            "image_url": image_url,
            "audio_url": audio_url,
        }
        self._log_operation("insert", "scenes", scene_data)
        try:
            response = self.client.table("scenes").insert(scene_data).execute()
            return bool(response.data)
        except Exception:
            logger.exception("Failed to create scene")
            raise

    # ... other scene methods


# storage.py
from typing import Union, Tuple, List, Dict, Any
from uuid import UUID
import io
import logging
import time

from .base import SupabaseBaseClient

logger = logging.getLogger(__name__)

class StorageService(SupabaseBaseClient):
    async def upload_file(self, bucket: str, path: str, content: bytes, mime: str) -> str:
        await self._ensure_bucket_exists(bucket)
        self.storage.from_(bucket).upload(
            path, content, file_options={"content-type": mime}
        )
        return self.storage.from_(bucket).get_public_url(path)

    async def _ensure_bucket_exists(self, bucket: str) -> None:
        try:
            self.storage.get_bucket(bucket)
        except Exception:
            self.storage.create_bucket(bucket, public_access=True)

    # ... other file methods


# health.py
import logging
import time

from .base import SupabaseBaseClient

logger = logging.getLogger(__name__)

class SupabaseHealthService(SupabaseBaseClient):
    async def check_connection(self) -> bool:
        try:
            self.client.table("users").select("user_id").limit(1).execute()
            return True
        except Exception:
            logger.exception("Supabase connection check failed")
            return False
