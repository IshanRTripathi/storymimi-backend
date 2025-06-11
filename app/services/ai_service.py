import base64
import json
import logging
from typing import Optional, Dict, Any

import httpx
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with AI APIs (OpenRouter, Together.ai, ElevenLabs)"""
    
    async def __aenter__(self):
        """Initialize the httpx client when entering the context manager"""
        self.client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the httpx client when exiting the context manager"""
        await self.client.aclose()
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text using OpenRouter.ai with Qwen model
        
        Args:
            prompt: The prompt to generate text from
            
        Returns:
            The generated text
            
        Raises:
            Exception: If the API call fails
        """
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
            response = await self.client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0  # Longer timeout for text generation
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.debug(f"Successfully generated text of length: {len(content)}")
            return content
        except Exception as e:
            # Log the error and re-raise
            logger.error(f"Error generating text: {str(e)}", exc_info=True)
            raise
    
    async def generate_image(self, prompt: str, width: int = 768, height: int = 432, 
                           steps: int = 12, seed: Optional[int] = None) -> bytes:
        """Generate an image using Together.ai with FLUX model
        
        Args:
            prompt: The prompt to generate the image from
            width: Width of the image
            height: Height of the image
            steps: Number of diffusion steps
            seed: Random seed for reproducibility
            
        Returns:
            Raw image bytes
            
        Raises:
            Exception: If the API call fails
        """
        logger.debug(f"Generating image with prompt length: {len(prompt)}, dimensions: {width}x{height}")
        
        headers = {
            "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.FLUX_MODEL_NAME,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
        }
        
        if seed is not None:
            payload["seed"] = seed
            logger.debug(f"Using seed: {seed} for image generation")
        
        try:
            logger.debug(f"Sending request to Together.ai API with model: {settings.FLUX_MODEL_NAME}")
            response = await self.client.post(
                f"{settings.TOGETHER_BASE_URL}/v1/image/create",
                headers=headers,
                json=payload,
                timeout=60.0  # Longer timeout for image generation
            )
            response.raise_for_status()
            
            data = response.json()
            logger.debug("Successfully received image data from Together.ai API")
            
            # Decode the base64 image
            image_data = base64.b64decode(data["output"]["data"][0])
            logger.debug(f"Successfully decoded image data, size: {len(image_data)} bytes")
            return image_data
        except Exception as e:
            # Log the error and re-raise
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
        logger.debug(f"Generating audio for text of length: {len(text)}, voice_id: {voice_id}")
        
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            logger.debug("Sending request to ElevenLabs API")
            response = await self.client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json=payload,
                timeout=60.0  # Longer timeout for audio generation
            )
            response.raise_for_status()
            
            # Return the raw audio bytes
            audio_content = response.content
            logger.debug(f"Successfully generated audio, size: {len(audio_content)} bytes")
            return audio_content
        except Exception as e:
            # Log the error and re-raise
            logger.error(f"Error generating audio: {str(e)}", exc_info=True)
            raise