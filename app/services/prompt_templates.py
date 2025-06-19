# Define required JSON structures for validation
STORY_STRUCTURE = {
    "child_profile": {
        "name": str,
        "age": int,
        "gender": str,
        "personality": list,
        "fears": list,
        "favorites": {
            "animal": str,
            "color": str,
            "toy": str
        },
        "physical_appearance": {
            "height": str,
            "build": str,
            "skin_tone": str,
            "hair_style": str,
            "hair_length": str,
            "hair_color": str,
            "accessory": str,
            "clothing": {
                "top": str,
                "bottom": str,
                "shoes": str
            }
        }
    },
    "side_character": {
        "exists": bool,
        "description": str,
        "relationship_to_main": str,
        "growth_arc": str
    },
    "story_meta": {
        "value_to_teach": str,
        "setting_description": str,
        "scene_count": int,
        "tone": str,
        "story_title": str,
        "target_age_range": str,
        "difficulty_level": str,
        "educational_concepts": list,
        "emotional_themes": list,
        "content_warnings": list,
        "readability_score": str
    },
    "scenes": [{
        "scene_number": int,
        "text": str,
        "prev_scene_summary": str,
        "time_of_day": str,
        "emotional_arc": str,
        "learning_checkpoints": list,
        "character_development": {
            "main_character_state": str,
            "side_character_state": str,
            "relationship_progress": str
        },
        "vocabulary_highlights": list
    }]
}

VISUAL_PROFILE_STRUCTURE = {
    "character_prompt": {
        "appearance_description": str,
        "emotional_state": str,
        "posture_and_movement": str,
        "lighting_preferences": str,
        "consistent_elements": list
    },
    "side_character_prompt": {
        "appearance_description": str,
        "relationship_positioning": str,
        "movement_style": str,
        "visual_personality": str
    },
    "scene_composition_guidelines": {
        "character_positioning": str,
        "perspective_preferences": str,
        "space_utilization": str,
        "background_integration": str
    },
    "color_palette": {
        "primary_colors": list,
        "accent_colors": list,
        "mood_specific_variations": {
            "happy": str,
            "calm": str,
            "excited": str
        }
    }
}

BASE_STYLE_STRUCTURE = {
    "base_style": {
        "art_style": str,
        "lighting": {
            "primary_source": str,
            "secondary_sources": str,
            "mood_lighting": str,
            "time_of_day_variations": str
        },
        "atmosphere": {
            "overall_mood": str,
            "weather_elements": str,
            "particle_effects": str,
            "depth_treatment": str
        },
        "color_scheme": {
            "primary_palette": str,
            "accent_colors": str,
            "mood_variations": str
        },
        "composition_rules": {
            "layout_grid": str,
            "focal_points": str,
            "depth_layers": str
        }
    }
}

SCENE_MOMENT_STRUCTURE = {
    "scene_moment": {
        "primary_action": str,
        "character_emotions": {
            "main_character": str,
            "side_character": str
        },
        "spatial_arrangement": {
            "character_positioning": str,
            "environmental_interaction": str,
            "depth_placement": str
        },
        "visual_emphasis": {
            "focal_point": str,
            "supporting_elements": str,
            "emotional_enhancers": str
        },
        "temporal_context": {
            "time_of_day": str,
            "weather_mood": str,
            "season_hints": str
        },
        "educational_integration": {
            "learning_elements": str,
            "value_reinforcement": str
        }
    }
}

# Prompt Templates from storygen.py, with explicit instruction to not format/beautify
STORY_PROMPT_TEMPLATE = """
You are a seasoned children's story writer and data extractor.

TASK:
1. Convert user input into structured JSON with:
   - child_profile: name, age, gender, personality (list), fears (list), favorites {{"animal", "color", "toy"}}, physical_appearance {{"height", "build", "skin_tone", "hair_style", "hair_length", "hair_color", "accessory", "clothing {{"top", "bottom", "shoes"}}}}
   - side_character: exists (true/false), description, relationship_to_main, growth_arc
   - story_meta: {{
       "value_to_teach": string,
       "setting_description": string,
       "scene_count": number,
       "tone": string,
       "story_title": string,
       "target_age_range": string,
       "difficulty_level": string,
       "educational_concepts": [string],
       "emotional_themes": [string],
       "content_warnings": [string],
       "readability_score": string
   }}
   - scenes: array of {{
       "scene_number": number,
       "text": string,
       "prev_scene_summary": string,
       "time_of_day": string,
       "emotional_arc": string,
       "learning_checkpoints": [string],
       "character_development": {{
           "main_character_state": string,
           "side_character_state": string,
           "relationship_progress": string
       }},
       "vocabulary_highlights": [string]
   }}

Ensure all fields are present and follow these requirements:
- scene_count [min:3, max:6]
- age [3,6]
- text [150-250 words per scene]
- accessory only one of [headband, headphones, glasses, bangles, bracelet, watch, etc]
- side_character only one of [animal, bird, fairy, balloon, etc]
- value_to_teach [kindness, empathy, thoughtfulness, love, extrovert, etc]
- readability_score must be age-appropriate
- vocabulary_highlights should include 3-5 age-appropriate words per scene
- emotional_arc must show clear progression
- learning_checkpoints must reinforce the value_to_teach
- time_of_day must be consistent and logical between scenes
- character_development must show gradual, meaningful change

IMPORTANT: 
- Each scene must have clear transitions and maintain narrative flow
- Emotional content must be age-appropriate and constructive
- Educational elements should be naturally woven into the story
- Content must be culturally sensitive and inclusive
- Return only raw, valid JSON, with no extra formatting or decoration

USER INPUT:
'''{user_input}'''
"""

VISUAL_PROFILE_PROMPT_TEMPLATE = """
You are a visual prompt specialist that provides in-depth detailed visual description for consistent story-telling.
INPUT:
{character_json}

OUTPUT JSON:
{{
    "character_prompt": {{
        "appearance_description": string,
        "emotional_state": string,
        "posture_and_movement": string,
        "lighting_preferences": string,
        "consistent_elements": [string]
    }},
    "side_character_prompt": {{
        "appearance_description": string,
        "relationship_positioning": string,
        "movement_style": string,
        "visual_personality": string
    }},
    "scene_composition_guidelines": {{
        "character_positioning": string,
        "perspective_preferences": string,
        "space_utilization": string,
        "background_integration": string
    }},
    "color_palette": {{
        "primary_colors": [string],
        "accent_colors": [string],
        "mood_specific_variations": {{
            "happy": string,
            "calm": string,
            "excited": string
        }}
    }}
}}

IMPORTANT: 
- All descriptions must maintain consistency across scenes
- Color choices must support emotional themes
- Visual elements must be age-appropriate
- Return only raw, valid JSON, with no extra formatting or decoration
"""

BASE_STYLE_PROMPT_TEMPLATE = """
You are an expert art director specializing in generating base/background for images for consistent story-telling.
INPUT:
- Setting description: {setting}
- Tone: {tone}

OUTPUT JSON:
{{
    "base_style": {{
        "art_style": string,
        "lighting": {{
            "primary_source": string,
            "secondary_sources": string,
            "mood_lighting": string,
            "time_of_day_variations": string
        }},
        "atmosphere": {{
            "overall_mood": string,
            "weather_elements": string,
            "particle_effects": string,
            "depth_treatment": string
        }},
        "color_scheme": {{
            "primary_palette": string,
            "accent_colors": string,
            "mood_variations": string
        }},
        "composition_rules": {{
            "layout_grid": string,
            "focal_points": string,
            "depth_layers": string
        }}
    }}
}}

IMPORTANT:
- Style must support emotional storytelling
- Lighting must enhance scene mood
- Colors must be age-appropriate and engaging
- Composition must guide young readers' attention
- Return only raw, valid JSON, with no extra formatting or decoration
"""

SCENE_MOMENT_PROMPT_TEMPLATE = """
You are a detailed image prompt writer for children's book scenes.
INPUT:
- Story so far: {story_so_far}
- Current scene text: {scene_text}

OUTPUT JSON:
{{
    "scene_moment": {{
        "primary_action": string,
        "character_emotions": {{
            "main_character": string,
            "side_character": string
        }},
        "spatial_arrangement": {{
            "character_positioning": string,
            "environmental_interaction": string,
            "depth_placement": string
        }},
        "visual_emphasis": {{
            "focal_point": string,
            "supporting_elements": string,
            "emotional_enhancers": string
        }},
        "temporal_context": {{
            "time_of_day": string,
            "weather_mood": string,
            "season_hints": string
        }},
        "educational_integration": {{
            "learning_elements": string,
            "value_reinforcement": string
        }}
    }}
}}

IMPORTANT:
- Scene must logically follow from previous events
- Character positions must be consistent with story
- Emotional expressions must match narrative
- Visual elements must support learning goals
- Return only raw, valid JSON, with no extra formatting or decoration
"""