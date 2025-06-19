import json
import logging
import time
import asyncio
import os
import requests
from typing import Any, Dict, Optional, Union
import httpx
from app.config import settings
from app.models.story_types import StoryRequest, Scene
from app.utils.json_sanitizer import validate_and_parse_llm_json, retry_on_json_error, validate_json_structure, robust_llm_schema_parse, repair_json_with_json_repair
import base64
import re
from app.utils.prompt_limits import get_component_limit, get_model_limits, MAX_TOTAL_PROMPT_LENGTH, PROMPT_COMPONENT_ALLOCATIONS, MODEL_SPECIFIC_LIMITS
from app.services.prompt_templates import STORY_PROMPT_TEMPLATE, VISUAL_PROFILE_PROMPT_TEMPLATE, BASE_STYLE_PROMPT_TEMPLATE, SCENE_MOMENT_PROMPT_TEMPLATE, STORY_STRUCTURE, VISUAL_PROFILE_STRUCTURE, BASE_STYLE_STRUCTURE, SCENE_MOMENT_STRUCTURE
from app.services.gemini_prompt_service import GeminiPromptService

logger = logging.getLogger(__name__)

LLM_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
LLM_LOG_FILE = os.path.join(LLM_LOG_DIR, 'llm_responses.log')
if not os.path.exists(LLM_LOG_DIR):
    os.makedirs(LLM_LOG_DIR)

llm_file_logger = logging.getLogger('llm_responses')
llm_file_logger.setLevel(logging.INFO)
if not llm_file_logger.handlers:
    fh = logging.FileHandler(LLM_LOG_FILE)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    llm_file_logger.addHandler(fh)

# Helper to log LLM responses
def log_llm_response(context: str, prompt: str, response: str):
    llm_file_logger.info(f"[LLM] Context: {context}\nPrompt: {prompt}\nResponse: {response}\n{'-'*80}")
    # logger.info(f"[LLM] Context: {context}\nPrompt: {prompt}\nResponse: {response}\n{'-'*80}")

class StoryPromptService:
    """
    Service for generating various LLM prompts and interacting with OpenRouter or Gemini.
    """
    def __init__(self):
        self.llm_backend = getattr(settings, "LLM_BACKEND", "openrouter")
        self.openrouter_base_url = settings.OPENROUTER_BASE_URL
        self.openrouter_api_key = settings.OPENROUTER_API_KEY
        self.timeout = 100 # From storygen.py
        self.max_retries = 3 # From storygen.py

        # LLM Model names from storygen.py
        self.story_model = settings.STORY_MODEL
        self.visual_profile_model = settings.VISUAL_PROFILE_MODEL
        self.base_style_model = settings.BASE_STYLE_MODEL
        self.scene_moment_model = settings.SCENE_MOMENT_MODEL

        # Gemini integration
        self.gemini_system_instruction = (
            "You are a seasoned children's story writer and data extractor.\n"
            "Return only raw, valid JSON, with no extra formatting or decoration.\n"
            "Do NOT use markdown, code blocks, or any formatting. Output ONLY valid JSON, nothing else."
        )
        self.gemini_service = GeminiPromptService(system_instruction=self.gemini_system_instruction)

    async def _call_llm(self, prompt: str, model: str) -> dict:
        if self.llm_backend == "gemini":
            # Gemini expects system/user split, so prompt is just the user part
            response_text = self.gemini_service.generate(prompt)
            return {"choices": [{"message": {"content": response_text}}]}
        headers = {"Authorization": f"Bearer {self.openrouter_api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        backoff = 1
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(f"[🔁 LLM Attempt {attempt}] Calling OpenRouter model: {model}")
                    resp = await client.post(f"{self.openrouter_base_url}/chat/completions", 
                                          headers=headers, 
                                          json=payload)
                    resp.raise_for_status()
                    logger.info(f"[✅ LLM Attempt {attempt} success] Response received from {model}")
                    log_llm_response('call_llm', prompt, str(resp.json()))
                    return resp.json()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(f"[LLM Retry {attempt}] Error: {str(e)}, retrying {model} in {backoff}s...")
                    if attempt == self.max_retries:
                        logger.error(f"[LLM Failed] {model} failed after {self.max_retries} retries: {str(e)}")
                        raise RuntimeError(f"LLM call to {model} failed after {self.max_retries} retries: {str(e)}")
                    await asyncio.sleep(backoff)
                    backoff *= 2

    async def _llm_fix_json(self, fix_prompt: str, original_json: str) -> str:
        """
        Use the same LLM backend to fix invalid JSON. Returns the LLM's response as a string.
        """
        if self.llm_backend == "gemini":
            from app.services.gemini_prompt_service import GeminiPromptService
            gemini = GeminiPromptService(system_instruction="You are a JSON fixer. Return only valid JSON.")
            return await asyncio.to_thread(gemini.generate, fix_prompt)
        else:
            # OpenRouter or other backend
            payload = {"model": self.story_model, "messages": [{"role": "user", "content": fix_prompt}]}
            # Use httpx for async
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.openrouter_base_url, headers={"Authorization": f"Bearer {self.openrouter_api_key}"}, json=payload)
                content = response.json()["choices"][0]["message"]["content"]
                return content

    @retry_on_json_error(max_retries=3)
    async def generate_structured_story(self, user_input: str) -> dict:
        """Async version of structured story generation."""
        prompt = STORY_PROMPT_TEMPLATE.format(user_input=user_input)
        response = await self._call_llm(prompt, self.story_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_structured_story', prompt, repair_json_with_json_repair(str(content)))
        story_data = await robust_llm_schema_parse(content, STORY_STRUCTURE, self._llm_fix_json)
        return story_data

    @retry_on_json_error(max_retries=3)
    async def generate_visual_profile(self, child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
        """Async version of visual profile generation with enhanced structure."""
        data = {**child_profile, **side_char}
        prompt = VISUAL_PROFILE_PROMPT_TEMPLATE.format(character_json=json.dumps(data))
        response = await self._call_llm(prompt, self.visual_profile_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_visual_profile', prompt, repair_json_with_json_repair(str(content)))
        visual_profile_json = validate_and_parse_llm_json(content)
        validate_json_structure(visual_profile_json, VISUAL_PROFILE_STRUCTURE)
        return visual_profile_json

    @retry_on_json_error(max_retries=3)
    async def generate_base_style(self, setting: str, tone: str) -> str:
        """Async version of base style generation."""
        prompt = BASE_STYLE_PROMPT_TEMPLATE.format(setting=setting, tone=tone)
        response = await self._call_llm(prompt, self.base_style_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_base_style', prompt, repair_json_with_json_repair(str(content)))
        base_style_json = validate_and_parse_llm_json(content)
        validate_json_structure(base_style_json, BASE_STYLE_STRUCTURE)
        # Format the base style into a descriptive string
        style = base_style_json["base_style"]
        base_style_str = (
            f"{style['art_style']} style with {style['lighting']['primary_source']} lighting, "
            f"creating a {style['atmosphere']['overall_mood']} atmosphere. "
            f"Using a {style['color_scheme']['primary_palette']} color palette "
            f"with {style['composition_rules']['focal_points']} focal points."
        )
        return base_style_str.strip()

    @retry_on_json_error(max_retries=3)
    async def generate_scene_moment(self, scene_text: str, story_so_far: str = "") -> str:
        """Async version of scene moment generation, with context for consistency."""
        prompt = SCENE_MOMENT_PROMPT_TEMPLATE.format(scene_text=scene_text, story_so_far=story_so_far)
        response = await self._call_llm(prompt, self.scene_moment_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_scene_moment', prompt, repair_json_with_json_repair(str(content)))
        scene_moment_json = validate_and_parse_llm_json(content)
        validate_json_structure(scene_moment_json, SCENE_MOMENT_STRUCTURE)
        # Format the scene moment into a descriptive string
        moment = scene_moment_json["scene_moment"]
        scene_moment_str = (
            f"{moment['primary_action']}, with {moment['character_emotions']['main_character']} "
            f"and {moment['character_emotions']['side_character']}. "
            f"{moment['spatial_arrangement']['character_positioning']} in "
            f"a {moment['temporal_context']['time_of_day']} setting, "
            f"emphasizing {moment['visual_emphasis']['focal_point']}."
        )
        return scene_moment_str.strip()

    def _build_image_prompt(self, scene_data: dict, style: str = "children's book illustration", model_name: str = 'stable_diffusion') -> str:
        """Build the image generation prompt with length limits for each component."""
        # Get component limits
        base_limit = get_component_limit('base_style')
        scene_limit = get_component_limit('scene')
        char_limit = get_component_limit('characters')
        atmos_limit = get_component_limit('atmosphere')
        tech_limit = get_component_limit('technical')
        # Build components with limits
        base_style = f"Base style: {style}"[:base_limit]
        scene_desc = f"Scene: {scene_data.get('setting', '')}. {scene_data.get('action', '')}"[:scene_limit]
        characters = f"Characters: {scene_data.get('characters', '')}"[:char_limit]
        atmosphere = (
            f"Atmosphere: {scene_data.get('time_of_day', '')}, "
            f"{scene_data.get('weather', '')}, {scene_data.get('mood', '')}"
        )[:atmos_limit]
        technical = (
            f"Technical details: High quality, detailed illustration, "
            f"balanced composition, dynamic lighting"
        )[:tech_limit]
        # Combine all components
        prompt = f"{base_style}. {scene_desc}. {characters}. {atmosphere}. {technical}"
        # Get model-specific and Scene model limits
        model_limits = get_model_limits(model_name)
        scene_model_max = Scene.model_fields['image_prompt'].max_length or 3000
        # Enforce the stricter of the two limits
        hard_limit = min(model_limits['max_length'], scene_model_max)
        if len(prompt) > hard_limit:
            logger.warning(f"[Prompt Truncation] Image prompt exceeded {hard_limit} chars. Truncating.")
            prompt = prompt[:hard_limit]
        return prompt 