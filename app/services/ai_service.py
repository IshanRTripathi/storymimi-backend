import base64
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

import httpx
from app.core.config.settings import settings
from app.services.story_prompt_service import StoryPromptService
from app.services.gemini_prompt_service import GeminiPromptService
from app.services.openrouter_service import OpenRouterService  # New modular service
from app.services.image_generation_service import ImageGenerationService  # New modular service
from app.services.audio_generation_service import AudioGenerationService  # New modular service

# Set up logging
logger = logging.getLogger(__name__)

class ElevenLabsTTSClient:
    """Modular ElevenLabs TTS client supporting v2 and v3, with robust error handling and logging."""
    def __init__(self, api_key: str, voice_id: str, use_v3: bool = False, timeout: int = 100, max_retries: int = 3):
        self.api_key = api_key
        self.voice_id = voice_id
        self.use_v3 = use_v3
        self.timeout = timeout
        self.max_retries = max_retries
        self.endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        self.output_format = "mp3_22050_32"  # can be made configurable

    async def generate_audio(self, text: str) -> bytes:
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {
            "text": text
        }
        if self.use_v3:
            payload["model_id"] = "eleven_v3"
            payload["voice_settings"] = {
                "stability": 0.7,
                "similarity_boost": 0.7,
                "style": 0.7,
                "use_speaker_boost": True
            }
        params = {"output_format": self.output_format}
        backoff = 1
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[ElevenLabsTTS] Attempt {attempt} | v3={self.use_v3} | Text len: {len(text)}")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.endpoint, headers=headers, json=payload, params=params)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", backoff))
                    logger.warning(f"[ElevenLabsTTS] 429 Rate Limit. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                logger.info(f"[ElevenLabsTTS] Success. Audio bytes: {len(resp.content)}")
                return resp.content
            except httpx.RequestError as e:
                logger.warning(f"[ElevenLabsTTS] Network error: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
            except httpx.HTTPStatusError as e:
                try:
                    error_payload = e.response.json()
                except Exception:
                    error_payload = e.response.text
                logger.error(f"[ElevenLabsTTS] HTTP error: {e}, payload: {error_payload}")
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", backoff))
                    logger.warning(f"[ElevenLabsTTS] 429 Rate Limit. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                raise
        raise RuntimeError(f"ElevenLabs TTS failed after {self.max_retries} retries")

class AIService:
    """
    Modular AIService for interacting with LLM, image, and audio APIs.
    """
    def __init__(self):
        self.llm_backend = getattr(settings, "LLM_BACKEND", "openrouter")
        self.timeout = 100
        self.max_retries = 3
        self.elevenlabs_use_v3 = getattr(settings, "ELEVENLABS_USE_V3", False)
        self.elevenlabs_tts = ElevenLabsTTSClient(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            use_v3=self.elevenlabs_use_v3,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        # Modular LLM backend selection
        if self.llm_backend == "gemini":
            self.llm_service = GeminiPromptService(system_instruction="You are a seasoned children's story writer and data extractor.")
        else:
            self.llm_service = OpenRouterService()
        # Modular image and audio services
        self.image_service = ImageGenerationService()
        self.audio_service = AudioGenerationService()

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    # Modular LLM API
    async def generate_text(self, prompt: str) -> str:
        return await self.llm_service.generate_text(prompt)

    async def generate_structured_story_llm(self, user_input: str) -> Dict[str, Any]:
        return await self.llm_service.generate_structured_story(user_input)

    async def generate_visual_profile_llm(self, child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
        return await self.llm_service.generate_visual_profile(child_profile, side_char)

    async def generate_base_style_llm(self, setting: str, tone: str) -> str:
        return await self.llm_service.generate_base_style(setting, tone)

    async def generate_scene_moment_llm(self, scene_text: str) -> str:
        return await self.llm_service.generate_scene_moment(scene_text)

    # Modular image generation
    async def generate_image(self, prompt: str, width: int = None, height: int = None, steps: int = 4, seed: Optional[int] = None, max_retries: int = 3) -> bytes:
        return await self.image_service.generate_image(prompt, width, height, steps, seed, max_retries)

    # Modular audio generation
    async def generate_audio(self, text: str, voice_id: str = None) -> bytes:
        return await self.audio_service.generate_audio(text, voice_id)

    async def _llm_rewrite_prompt(self, error_message: str, original_prompt: str) -> str:
        gemini = GeminiPromptService(system_instruction="You are a prompt fixer. Return only a revised prompt that avoids the error described.")
        fix_prompt = (
            f"The following image prompt caused an error: {error_message}\n"
            "Please rewrite the prompt to avoid this error. "
            "Make it 100% safe for children, G-rated, and free of any inappropriate or ambiguous content. "
            "Return only the revised prompt.\n"
            f"Prompt: {original_prompt}"
        )
        # You may want to move this to a utility or keep as is
        revised_prompt = await asyncio.to_thread(gemini.generate, fix_prompt)
        return revised_prompt