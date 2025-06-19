import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class AudioGenerationService:
    """
    Service for generating audio using ElevenLabs or other providers.
    """
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.use_v3 = getattr(settings, "ELEVENLABS_USE_V3", False)
        self.timeout = 100
        self.max_retries = 3

    async def generate_audio(self, text: str, voice_id: Optional[str] = None) -> bytes:
        voice_id = voice_id or self.voice_id
        endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        output_format = "mp3_22050_32"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        payload = {"text": text}
        if self.use_v3:
            payload["model_id"] = "eleven_v3"
            payload["voice_settings"] = {
                "stability": 0.7,
                "similarity_boost": 0.7,
                "style": 0.7,
                "use_speaker_boost": True
            }
        params = {"output_format": output_format}
        backoff = 1
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"[AudioGen] Attempt {attempt} | v3={self.use_v3} | Text len: {len(text)}")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(endpoint, headers=headers, json=payload, params=params)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", backoff))
                    logger.warning(f"[AudioGen] 429 Rate Limit. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                logger.info(f"[AudioGen] Success. Audio bytes: {len(resp.content)}")
                return resp.content
            except httpx.RequestError as e:
                logger.warning(f"[AudioGen] Network error: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
            except httpx.HTTPStatusError as e:
                try:
                    error_payload = e.response.json()
                except Exception:
                    error_payload = e.response.text
                logger.error(f"[AudioGen] HTTP error: {e}, payload: {error_payload}")
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", backoff))
                    logger.warning(f"[AudioGen] 429 Rate Limit. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    backoff *= 2
                    continue
                raise
        raise RuntimeError(f"Audio generation failed after {self.max_retries} retries") 