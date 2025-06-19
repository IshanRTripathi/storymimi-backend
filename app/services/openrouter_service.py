import logging
import httpx
from app.config import settings
from typing import Any, Dict

logger = logging.getLogger(__name__)

class OpenRouterService:
    """
    Service for interacting with OpenRouter LLM APIs.
    Interface matches GeminiPromptService for easy switching.
    """
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.story_model = settings.QWEN_MODEL_NAME
        self.visual_profile_model = getattr(settings, 'VISUAL_PROFILE_MODEL', self.story_model)
        self.base_style_model = getattr(settings, 'BASE_STYLE_MODEL', self.story_model)
        self.scene_moment_model = getattr(settings, 'SCENE_MOMENT_MODEL', self.story_model)
        self.timeout = 100
        self.max_retries = 3

    async def generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.story_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"[OpenRouter] Attempt {attempt} - Generating text")
                    resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    logger.warning(f"[OpenRouter] Attempt {attempt} failed: {e}")
                    if attempt == self.max_retries:
                        raise

    async def generate_structured_story(self, user_input: str) -> Dict[str, Any]:
        # This should use the same prompt template as the main app
        return await self.generate_text(user_input)

    async def generate_visual_profile(self, child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
        # Compose prompt as needed
        prompt = f"Generate a visual profile for: {child_profile}, {side_char}"
        return await self.generate_text(prompt)

    async def generate_base_style(self, setting: str, tone: str) -> str:
        prompt = f"Generate a base style for setting: {setting}, tone: {tone}"
        return await self.generate_text(prompt)

    async def generate_scene_moment(self, scene_text: str) -> str:
        prompt = f"Describe the key moment for this scene: {scene_text}"
        return await self.generate_text(prompt) 