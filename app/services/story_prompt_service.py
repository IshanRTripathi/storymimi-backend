import json
import logging
import time
import asyncio
import os
import requests
from typing import Any, Dict, Optional, Union
import httpx
from app.config import settings
from app.models.story_types import StoryRequest
import base64
import re

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

# Helper to clean LLM responses of markdown/code block/beautifying characters
def clean_llm_response(content: str) -> str:
    """
    Remove markdown/code block formatting and beautifying characters from LLM responses.
    Only strips wrapping formatting, not content inside JSON/strings.
    """
    content = content.strip()
    # Remove code block (``` or ```json)
    if content.startswith("```"):
        lines = content.splitlines()
        # Remove the first line if it starts with '```' or '```json'
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Remove the last line if it's just ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
    # Remove leading/trailing asterisks, underscores, tildes, etc (but not inside JSON)
    content = re.sub(r'^[*_~\s]+', '', content)
    content = re.sub(r'[*_~\s]+$', '', content)
    return content

class StoryPromptService:
    """
    Service for generating various LLM prompts and interacting with OpenRouter.
    """
    def __init__(self):
        self.openrouter_base_url = settings.OPENROUTER_BASE_URL
        self.openrouter_api_key = settings.OPENROUTER_API_KEY
        self.timeout = 100 # From storygen.py
        self.max_retries = 3 # From storygen.py

        # LLM Model names from storygen.py
        self.story_model = settings.STORY_MODEL
        self.visual_profile_model = settings.VISUAL_PROFILE_MODEL
        self.base_style_model = settings.BASE_STYLE_MODEL
        self.scene_moment_model = settings.SCENE_MOMENT_MODEL

        # Prompt Templates from storygen.py, with explicit instruction to not format/beautify
        self.STORY_PROMPT_TEMPLATE = """
You are a seasoned children's story writer and data extractor.

TASK:
1. Convert user input into structured JSON with:
   - child_profile: name, age, gender, personality (list), fears (list), favorites {{animal, color, toy}}, physical_appearance {{height, build, skin_tone, hair_style, hair_length, hair_color, accessories, clothing {{top, bottom, shoes}}}}
   - side_character: exists (true/false), description
   - story_meta: value_to_teach, setting_description, scene_count, tone, story_title
   - scenes: array of {{scene_number, text, prev_scene_summary}}
   - text has a very well detailed description of the scene and the action happening in the scene with consistency.
   - prev_scene_summary (empty for 1st scene) has a very concise description of the previous scene and the action happening in the previous scene for consistency in current scene.

Ensure all fields are present; autofill with relevant values in case not provided.
scene_count [3,5]
age [3,6]
text [700-1000 words]
accessories [headband, headphones, glasses, bangles, bracelet, watch]
side_character [animal, bird, fairy, robot, balloon]
value_to_teach [kindness, empathy, thoughfulness, love, extrovert]

IMPORTANT: Do NOT format the response as markdown, code block, or with any beautifying characters. Return only raw, valid JSON, with no extra formatting or decoration.

USER INPUT:
'''{user_input}'''
"""

        self.VISUAL_PROFILE_PROMPT_TEMPLATE = """
You are a visual prompt specialist that provides in depth detailed visual description for consistent story-telling.
INPUT:
{character_json}

OUTPUT JSON:
- character_prompt: describing the child's appearance, outfit, and distinguishing features in detail required for consistency.
- side_character_prompt: one sentence describing the side character or toy's appearance and presence, color, structure.

IMPORTANT: Do NOT format the response as markdown, code block, or with any beautifying characters. Return only raw, valid JSON, with no extra formatting or decoration.
"""

        self.BASE_STYLE_PROMPT_TEMPLATE = """
You are an expert art director that has speciality in generating base/background for images for consistent story-telling.
INPUT:
- Setting description: {setting}
- Tone: {tone}

OUTPUT:
Base prompt describing the visual style (mood, lighting, art style, color palette) to be applied consistently across all scenes along with specific art style.
art style select one from anime, pixar, ghibli, watercolour, etc. Number of words should be around 40.

IMPORTANT: Do NOT format the response as markdown, code block, or with any beautifying characters. Return only the raw string, with no extra formatting or decoration.
"""

        self.SCENE_MOMENT_PROMPT_TEMPLATE = """
You are a detailed image prompt writer for children's book scenes.
INPUT:
- Story so far: {story_so_far}
- Current scene text: {scene_text}

OUTPUT:
One descriptive phrase capturing the visual moment/action for this scene. Add elements like actions performed by the character or side character based on the scene text instead of just making the character doing a single pose across all scenes. Ensure the scene is consistent and believable, logically following from previous events and the story context. Do not contradict earlier scenes.

IMPORTANT: Do NOT format the response as markdown, code block, or with any beautifying characters. Return only the raw string, with no extra formatting or decoration.
"""

    async def _call_llm(self, prompt: str, model: str) -> Dict[str, Any]:
        """Async version of LLM call for backward compatibility."""
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

    async def generate_structured_story(self, user_input: str) -> Dict[str, Any]:
        """Async version of structured story generation."""
        prompt = self.STORY_PROMPT_TEMPLATE.format(user_input=user_input)
        response = await self._call_llm(prompt, self.story_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_structured_story', prompt, str(content))
        content = clean_llm_response(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured story JSON: {e}, raw content: {content}")
            raise ValueError("LLM returned invalid JSON for structured story.") from e

    async def generate_visual_profile(self, child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
        """Async version of visual profile generation."""
        data = {**child_profile, **side_char}
        prompt = self.VISUAL_PROFILE_PROMPT_TEMPLATE.format(character_json=json.dumps(data))
        response = await self._call_llm(prompt, self.visual_profile_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_visual_profile', prompt, str(content))
        content = clean_llm_response(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse visual profile JSON: {e}, raw content: {content}")
            raise ValueError("LLM returned invalid JSON for visual profile.") from e

    async def generate_base_style(self, setting: str, tone: str) -> str:
        """Async version of base style generation."""
        prompt = self.BASE_STYLE_PROMPT_TEMPLATE.format(setting=setting, tone=tone)
        response = await self._call_llm(prompt, self.base_style_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_base_style', prompt, str(content))
        content = clean_llm_response(content)
        return content.strip().strip('"')

    async def generate_scene_moment(self, scene_text: str, story_so_far: str = "") -> str:
        """Async version of scene moment generation, with context for consistency."""
        prompt = self.SCENE_MOMENT_PROMPT_TEMPLATE.format(scene_text=scene_text, story_so_far=story_so_far)
        response = await self._call_llm(prompt, self.scene_moment_model)
        content = response["choices"][0]["message"]["content"]
        log_llm_response('generate_scene_moment', prompt, str(content))
        content = clean_llm_response(content)
        return content.strip().strip('"') 