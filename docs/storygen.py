import os
import json
import time
import requests
import base64
from typing import Dict, Any, Optional, List

# --- CONFIGURATION ---
OPENROUTER_API_KEY = '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'
TOGETHER_API_KEY = '75fbddb409506426c6cb0c316afc1b5516963190352037f03a993e966022f334'

# LLM Models
STORY_MODEL = "qwen/qwen3-30b-a3b:free"
VISUAL_PROFILE_MODEL = "qwen/qwen3-30b-a3b:free"
BASE_STYLE_MODEL = "qwen/qwen3-30b-a3b:free"
SCENE_MOMENT_MODEL = "qwen/qwen3-30b-a3b:free"

# Together Image API
TOGETHER_API_URL = "https://api.together.xyz/v1/images/generations"
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell-Free"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 768

# Retry settings
MAX_RETRIES = 3
TIMEOUT = 100

# --- PROMPT TEMPLATES ---
STORY_PROMPT_TEMPLATE = '''
You are a seasoned children's story writer and data extractor.

TASK:
1. Convert user input into structured JSON with:
   - child_profile: name, age, gender, personality (list), fears (list), favorites {{animal, color, toy}}, physical_appearance {{height, build, skin_tone, hair_style, hair_length, hair_color, accessories, clothing {{top, bottom, shoes}}}}
   - side_character: exists (true/false), description
   - story_meta: value_to_teach, setting_description, scene_count, tone, story_title
   - scenes: array of {{scene_number, text}}

Ensure all fields are present; autofill with relevant values in case not provided.
scene_count [3,5]
age [3,6]
accessories [headband, headphones, glasses, bangles, bracelet, watch]
side_character [animal, bird, fairy, robot, balloon]
value_to_teach [kindness, empathy, thoughfulness, love, extrovert]
Return ONLY valid JSON.

USER INPUT:
"""{user_input}"""
'''

VISUAL_PROFILE_PROMPT_TEMPLATE = '''
You are a visual prompt specialist that provides in depth detailed visual description for story-telling.
INPUT:
{character_json}

OUTPUT JSON:
- character_prompt: one concise sentence describing the child’s appearance, outfit, and distinguishing details.
- side_character_prompt: one sentence describing the side character or toy’s appearance and presence, color, structure.
'''

BASE_STYLE_PROMPT_TEMPLATE = '''
You are an expert art director that has speciality in generating base for images.
INPUT:
- Setting description: {setting}
- Tone: {tone}

OUTPUT:
One detailed base prompt describing the visual style (mood, lighting, art style, color palette) to be applied consistently across all scenes along with specific art style from anime, pixar, ghibli, watercolour, etc. Return only the prompt string.
'''

SCENE_MOMENT_PROMPT_TEMPLATE = '''
You are a concise image prompt writer for children's book scenes.
INPUT:
{scene_text}

OUTPUT:
One descriptive phrase capturing the visual moment/action for this scene. Add elements like actions performed by the character or side character based on the scene text. Return only the phrase.
'''

# --- CORE FUNCTIONS ---
def call_openrouter(prompt: str, model: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    backoff = 1
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[🔁 LLM Attempt {attempt}] Calling OpenRouter model with prompt {payload}")
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            print(f"[✅ LLM Attempt {attempt} success] Response {resp.json}")
            return resp.json()
        except requests.RequestException as e:
            print(f"[LLM Retry {attempt}] {e}, retrying in {backoff}s...")
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError("LLM call failed after retries")


def generate_story(user_input: str) -> Dict[str, Any]:
    prompt = STORY_PROMPT_TEMPLATE.format(user_input=user_input)
    resp = call_openrouter(prompt, STORY_MODEL)
    return json.loads(resp["choices"][0]["message"]["content"])


def generate_visual_profile(child_profile: Dict[str, Any], side_char: Dict[str, Any]) -> Dict[str, str]:
    data = {**child_profile, **side_char}
    prompt = VISUAL_PROFILE_PROMPT_TEMPLATE.format(character_json=json.dumps(data))
    resp = call_openrouter(prompt, VISUAL_PROFILE_MODEL)
    return json.loads(resp["choices"][0]["message"]["content"])


def generate_base_style(setting: str, tone: str) -> str:
    prompt = BASE_STYLE_PROMPT_TEMPLATE.format(setting=setting, tone=tone)
    resp = call_openrouter(prompt, BASE_STYLE_MODEL)
    return resp["choices"][0]["message"]["content"].strip().strip('"')


def generate_scene_moment(scene_text: str) -> str:
    prompt = SCENE_MOMENT_PROMPT_TEMPLATE.format(scene_text=scene_text)
    response = call_openrouter(prompt, SCENE_MOMENT_MODEL)
    return response["choices"][0]["message"]["content"].strip().strip('"')


def generate_image_together(full_prompt: str, scene_num: int) -> Optional[str]:
    payload = {
        "model": IMAGE_MODEL,
        "prompt": full_prompt,
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
        "steps": 4,
        "n": 1,
        "response_format": "b64_json"
    }
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
    backoff = 1
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[🖼️ Scene {scene_num} | Attempt {attempt}] Sending to Together API...")
            resp = requests.post(TOGETHER_API_URL, headers=headers, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()["data"][0]
            return data.get("b64_json")
        except requests.RequestException as e:
            print(f"[Image Retry {attempt}] {e}, retrying in {backoff}s...")
            time.sleep(backoff)
            backoff *= 2
    return None


def save_image(b64: str, path: str):
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))

# --- MAIN WORKFLOW ---
if __name__ == "__main__":
    user_input = input("Enter story details as freeform text:\n\n")

    print("\n[1/5] Generating structured story...")
    story = generate_story(user_input)
    print("✅ Story structured.")

    child_profile = story["child_profile"]
    side_char = story.get("side_character", {})
    meta = story["story_meta"]
    setting = meta["setting_description"]
    tone = meta.get("tone", "warm and whimsical")
    scenes = story["scenes"]

    print("\n[2/5] Generating visual profile...")
    vis = generate_visual_profile(child_profile, side_char)
    child_desc = vis["character_prompt"]
    side_desc = vis.get("side_character_prompt", "")
    print("✅ Visual profile ready.")

    print("\n[3/5] Generating base style prompt...")
    base_style = generate_base_style(setting, tone)
    print(f"✅ Base style prompt: {base_style}\n")

    print(f"[4/5] Processing {len(scenes)} scenes...\n")
    for scene in scenes:
        num = scene["scene_number"]
        text = scene["text"]
        print(f"➡️ Scene {num}: Generating scene moment...")
        moment = generate_scene_moment(text)
        full_prompt = f"Base style: {base_style}. In {setting}, {story['child_profile']['name']}, {child_desc}, {moment} {side_desc}".strip()
        with open(f"scene_{num}_prompt.json", "w") as f:
            json.dump({"full_prompt": full_prompt}, f, indent=2)
        print(f"[📄] scene_{num}_prompt.json created ({len(full_prompt)} chars)")

        print(f"🖼️ Scene {num}: Generating image...")
        b64 = generate_image_together(full_prompt, num)
        if b64:
            fname = f"scene_{num}.png"
            save_image(b64, fname)
            print(f"✅ scene_{num}.png saved.\n")
        else:
            print(f"❌ scene_{num} image failed.\n")

    print("[5/5] Workflow complete!")
