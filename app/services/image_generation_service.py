import base64
import logging
import httpx
from typing import Optional
from app.core.config.settings import settings

logger = logging.getLogger(__name__)

class ImageGenerationService:
    """
    Service for generating images using Together.ai (FLUX) or other providers.
    """
    def __init__(self):
        self.api_url = settings.TOGETHER_API_URL
        self.api_key = settings.TOGETHER_API_KEY
        self.model = settings.IMAGE_MODEL
        self.default_width = settings.IMAGE_WIDTH
        self.default_height = settings.IMAGE_HEIGHT
        self.timeout = 100
        self.max_retries = 3

    async def generate_image(self, prompt: str, width: int = None, height: int = None, steps: int = 4, seed: Optional[int] = None, max_retries: int = 3) -> bytes:
        width = width if width is not None else self.default_width
        height = height if height is not None else self.default_height
        safe_prompt = prompt + "\nThis image must be safe for children. No nudity, violence, or inappropriate content. G-rated. Wholesome. No NSFW elements."
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "prompt": safe_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "response_format": "b64_json"
        }
        if seed is not None:
            payload["seed"] = seed
            logger.debug(f"Using seed: {seed} for image generation")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(max_retries):
                try:
                    logger.debug(f"[ImageGen] Attempt {attempt+1} - Sending request to Together.ai API with model: {self.model}")
                    resp = await client.post(self.api_url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    image_data = base64.b64decode(data["data"][0].get("b64_json", ""))
                    if not image_data or len(image_data) < 100:
                        logger.error("Invalid image data received from Together.ai API")
                        raise ValueError("Invalid image data from API")
                    logger.debug(f"Successfully decoded image data, size: {len(image_data)} bytes")
                    return image_data
                except Exception as e:
                    logger.warning(f"[ImageGen] Attempt {attempt+1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise 