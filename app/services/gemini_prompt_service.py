import google.generativeai as genai
import os
import logging
from app.core.config.settings import settings

logger = logging.getLogger(__name__)

class GeminiPromptService:
    def __init__(self, system_instruction: str, temperature=0.8, top_p=0.95, max_output_tokens=2048):
        api_key = settings.GEMINI_API_KEY
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)  # or "gemini-1.5-pro", "gemini-1.0-pro"
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens

    def generate(self, user_prompt: str) -> str:
        full_prompt = self.system_instruction + "\n\n" + user_prompt
        response = self.model.generate_content(
            full_prompt,
            generation_config={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_output_tokens": self.max_output_tokens,
            },
        )
        logger.info(f"Gemini response: {response.text}")
        return response.text 