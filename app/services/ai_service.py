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
        """Internal method to call an external API with retry logic."""
        backoff = 1
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[API Attempt {attempt}] Calling {method.upper()} {url}")
                if method == "post":
                    if content_type == "application/json":
                        resp = await self.client.post(url, headers=headers, json=json_data)
                    else:
                        resp = await self.client.post(url, headers=headers, content=json_data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                resp.raise_for_status()
                logger.info(f"[API Attempt {attempt} success] Response received from {url}")
                return resp
            except httpx.RequestError as e:
                logger.warning(f"[API Retry {attempt}] {e}, retrying {url} in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
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
    
    async def generate_audio(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> bytes:
        """Generate audio using ElevenLabs API
        
        Args:
            text: The text to convert to speech
            voice_id: The ID of the voice to use
            
        Returns:
            Raw audio bytes
            
        Raises:
            Exception: If the API call fails
        """
        if settings.USE_MOCK_AI_SERVICES:
            logger.info("Using mock audio generation")
            return await self.mock_service.generate_audio(text, voice_id)
        
        logger.info(f"Generating audio with ElevenLabs V3 for text length: {len(text)}")
        logger.debug(f"Using voice_id: {voice_id}")
        
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        
        # V3-specific settings for storytelling
        payload = {
            "text": text,
            "model_id": "eleven_v3",
            "voice_settings": {
                "stability": 0.7,  # Creative mode for more expressiveness
                "similarity_boost": 0.7,
                "style": 0.7,  # New in V3
                "use_speaker_boost": True  # Better voice consistency
            }
        }
        
        try:
            logger.debug("Sending request to ElevenLabs V3 API")
            response = await self._call_api_with_retries(
                "post", 
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json_data=payload
            )
            
            audio_content = response.content
            if not audio_content or len(audio_content) < 100:
                logger.error("Invalid audio content received from ElevenLabs API")
                raise ValueError("Invalid audio content from API")
                
            logger.info(f"Successfully generated audio, size: {len(audio_content)} bytes")
            return audio_content
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}", exc_info=True)
            raise