import base64
import json
import logging
import asyncio
from typing import Optional, Dict, Any

import httpx
from app.config import settings
from app.mocks.mock_ai_service import MockAIService
from app.services.story_prompt_service import StoryPromptService

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
    """Service for interacting with AI APIs (OpenRouter, Together.ai, ElevenLabs)"""
    
    def __init__(self):
        """Initialize the service with either real or mock implementation"""
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock AI service implementation")
            self.mock_service = MockAIService(settings.MOCK_DELAY_SECONDS)
        else:
            logger.info("Using real AI service implementation")
            self.story_prompt_service = StoryPromptService()
        self.timeout = 100
        self.max_retries = 3
        # ElevenLabs feature flag
        self.elevenlabs_use_v3 = getattr(settings, "ELEVENLABS_USE_V3", False)
        self.elevenlabs_tts = ElevenLabsTTSClient(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            use_v3=self.elevenlabs_use_v3,
            timeout=self.timeout,
            max_retries=self.max_retries
        )

    async def __aenter__(self):
        """Initialize the httpx client when entering the context manager"""
        if settings.USE_MOCK_AI_SERVICES:
            return self.mock_service
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the httpx client when exiting the context manager"""
        if settings.USE_MOCK_AI_SERVICES:
            return
        await self.client.aclose()
    
    async def _call_api_with_retries(self, method: str, url: str, headers: Dict, json_data: Dict = None, content_type: str = "application/json") -> httpx.Response:
        """Internal method to call an external API with retry logic, 429 handling, and error logging."""
        backoff = 1
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[API Attempt {attempt}] Calling {method.upper()} {url}")
                if method == "post":
                    if content_type == "application/json":
                        resp = await self.client.post(url, headers=headers, json=json_data)
                    else:
                        resp = await self.client.post(url, headers=headers, content=json_data)
                elif method == "get":
                    resp = await self.client.get(url, headers=headers, params=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", backoff))
                    logger.warning(f"[API Rate Limit] 429 received. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                logger.info(f"[API Attempt {attempt} success] Response received from {url}")
                return resp
            except httpx.RequestError as e:
                logger.warning(f"[API Retry {attempt}] {e}, retrying {url} in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
            except httpx.HTTPStatusError as e:
                # Log error payload if available
                try:
                    error_payload = e.response.json()
                except Exception:
                    error_payload = e.response.text
                logger.error(f"[API Error] {e}, payload: {error_payload}")
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", backoff))
                    logger.warning(f"[API Rate Limit] 429 received. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                raise
        raise RuntimeError(f"API call to {url} failed after {self.max_retries} retries")

    async def generate_text(self, prompt: str) -> str:
        """Generate text using OpenRouter.ai with Qwen model
        
        Args:
            prompt: The prompt to generate text from
            
        Returns:
            The generated text
            
        Raises:
            Exception: If the API call fails
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock text generation")
            return await self.mock_service.generate_text(prompt)
        
        logger.debug(f"Generating text with prompt length: {len(prompt)}")
        
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.QWEN_MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        
        try:
            logger.debug(f"Sending request to OpenRouter API with model: {settings.QWEN_MODEL_NAME}")
            response = await self._call_api_with_retries("post", f"{settings.OPENROUTER_BASE_URL}/chat/completions", headers=headers, json_data=payload)
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.debug(f"Successfully generated text of length: {len(content)}")
            return content
        except Exception as e:
            # Log the error and re-raise
            logger.error(f"Error generating text: {str(e)}", exc_info=True)
            raise
    
    async def generate_structured_story_llm(self, user_input: str) -> Dict[str, Any]:
        """
        Generates a structured story JSON using LLM via StoryPromptService.
        Handles mock service delegation.
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock structured story generation")
            return await self.mock_service.generate_structured_story(user_input)
        else:
            logger.info("Using real structured story generation via StoryPromptService")
            return await self.story_prompt_service.generate_structured_story(user_input)

    async def generate_visual_profile_llm(self, child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates visual prompts for child and side characters using LLM via StoryPromptService.
        Handles mock service delegation.
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock visual profile generation")
            return await self.mock_service.generate_visual_profile(child_profile, side_char)
        else:
            logger.info("Using real visual profile generation via StoryPromptService")
            return await self.story_prompt_service.generate_visual_profile(child_profile, side_char)

    async def generate_base_style_llm(self, setting: str, tone: str) -> str:
        """
        Generates a base visual style prompt using LLM via StoryPromptService.
        Handles mock service delegation.
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock base style generation")
            return await self.mock_service.generate_base_style(setting, tone)
        else:
            logger.info("Using real base style generation via StoryPromptService")
            return await self.story_prompt_service.generate_base_style(setting, tone)

    async def generate_scene_moment_llm(self, scene_text: str) -> str:
        """
        Generates a descriptive phrase for a single scene's visual moment/action using LLM via StoryPromptService.
        Handles mock service delegation.
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock scene moment generation")
            return await self.mock_service.generate_scene_moment(scene_text)
        else:
            logger.info("Using real scene moment generation via StoryPromptService")
            return await self.story_prompt_service.generate_scene_moment(scene_text)

    async def generate_image(self, prompt: str, width: int = None, height: int = None, 
                           steps: int = 4, seed: Optional[int] = None) -> bytes:
        """Generate an image using Together.ai with FLUX model
        
        Args:
            prompt: The prompt to generate the image from
            width: Width of the image (defaults to config setting)
            height: Height of the image (defaults to config setting)
            steps: Number of diffusion steps (defaults to 4)
            seed: Random seed for reproducibility
            
        Returns:
            Raw image bytes
            
        Raises:
            Exception: If the API call fails
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock image generation")
            return await self.mock_service.generate_image(prompt, width, height, steps, seed)
        
        width = width if width is not None else settings.IMAGE_WIDTH
        height = height if height is not None else settings.IMAGE_HEIGHT

        logger.debug(f"Generating image with prompt length: {len(prompt)}, dimensions: {width}x{height}")
        
        headers = {
            "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.IMAGE_MODEL,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "response_format": "b64_json"
        }
        
        if seed is not None:
            payload["seed"] = seed
            logger.debug(f"Using seed: {seed} for image generation")
        
        try:
            logger.debug(f"Sending request to Together.ai API with model: {settings.IMAGE_MODEL}")
            response = await self._call_api_with_retries("post", settings.TOGETHER_API_URL, headers=headers, json_data=payload)
            
            data = response.json()
            logger.debug("Successfully received image data from Together.ai API")
            
            try:
                image_data = base64.b64decode(data["data"][0].get("b64_json", ""))
                if not image_data or len(image_data) < 100:
                    logger.error("Invalid image data received from Together.ai API")
                    raise ValueError("Invalid image data from API")
                logger.debug(f"Successfully decoded image data, size: {len(image_data)} bytes")
                return image_data
            except Exception as decode_error:
                logger.error(f"Failed to decode image data: {str(decode_error)}")
                raise ValueError(f"Failed to decode image data: {str(decode_error)}") from decode_error
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            raise
    
    async def generate_audio(self, text: str, voice_id: str = None) -> bytes:
        """Generate audio using ElevenLabs API (v2 or v3, feature-flagged)."""
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock audio generation")
            return await self.mock_service.generate_audio(text, voice_id or settings.ELEVENLABS_VOICE_ID)
        # Use the modular TTS client
        if voice_id and voice_id != self.elevenlabs_tts.voice_id:
            # If a different voice is requested, create a temp client
            tts_client = ElevenLabsTTSClient(
                api_key=settings.ELEVENLABS_API_KEY,
                voice_id=voice_id,
                use_v3=self.elevenlabs_use_v3,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
            return await tts_client.generate_audio(text)
        return await self.elevenlabs_tts.generate_audio(text)