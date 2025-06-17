# ElevenLabs V3 Integration Guide

## Overview

ElevenLabs V3 introduces significant improvements in voice quality and expressiveness, making it ideal for storytelling applications. This document outlines how to leverage these features for creating engaging story narrations.

## Key Features of V3

1. **Enhanced Voice Control**
   - Stability: 0-1 scale (0.7 recommended for storytelling)
   - Similarity Boost: Voice consistency control
   - Style: New parameter for emotional expression
   - Speaker Boost: Improved voice clarity

2. **Expressive Tags**
   ```
   [excited] For high-energy moments
   [whispered] For quiet or secretive parts
   [serious] For important revelations
   [shouted] For dramatic emphasis
   [laughing] For joyful moments
   ```

3. **Sound Effects**
   ```
   [sound:footsteps]
   [sound:door_creak]
   [sound:thunder]
   ```

## Implementation Guide

1. **Voice Settings**
   ```python
   voice_settings = {
       "stability": 0.7,        # More expressive
       "similarity_boost": 0.7,  # Good voice consistency
       "style": 0.7,            # Enhanced emotional range
       "use_speaker_boost": True # Better clarity
   }
   ```

2. **Scene Processing**
   ```python
   def process_scene_for_narration(scene_text: str, mood: str) -> str:
       # Add emotional context
       if "excited" in mood:
           scene_text = f"[excited] {scene_text}"
       elif "mysterious" in mood:
           scene_text = f"[whispered] {scene_text}"
           
       # Add sound effects
       if "door" in scene_text.lower():
           scene_text = f"[sound:door_creak] {scene_text}"
           
       return scene_text
   ```

3. **API Integration**
   ```python
   async def generate_audio(text: str, voice_id: str) -> bytes:
       url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
       headers = {
           "xi-api-key": settings.ELEVENLABS_API_KEY,
           "Content-Type": "application/json"
       }
       payload = {
           "text": text,
           "model_id": "eleven_v3",
           "voice_settings": voice_settings
       }
       response = await make_request(url, headers, payload)
       return response.content
   ```

## Best Practices

1. **Scene Analysis**
   - Analyze scene content for emotional context
   - Identify key moments for sound effects
   - Consider character dialogue and perspective

2. **Voice Selection**
   - Choose voices that match character age/gender
   - Test voices with different emotional tags
   - Consider using multiple voices for dialogue

3. **Performance Optimization**
   - Cache frequently used audio segments
   - Implement retry logic for API calls
   - Monitor audio generation timing

## Expressive Narration Guide

1. **Emotional Mapping**
   ```python
   EMOTION_TAGS = {
       "happy": "[excited]",
       "sad": "[gentle]",
       "scared": "[nervous]",
       "angry": "[intense]",
       "surprised": "[shocked]"
   }
   ```

2. **Scene Mood Detection**
   ```python
   def detect_scene_mood(text: str) -> str:
       # Use sentiment analysis or keyword matching
       if any(word in text.lower() for word in ["laugh", "smile", "joy"]):
           return "happy"
       elif any(word in text.lower() for word in ["scared", "fear", "dark"]):
           return "scared"
       return "neutral"
   ```

3. **Dynamic Voice Adjustment**
   ```python
   def adjust_voice_settings(mood: str) -> Dict:
       if mood == "happy":
           return {"stability": 0.6, "style": 0.8}  # More expressive
       elif mood == "scared":
           return {"stability": 0.8, "style": 0.6}  # More controlled
       return {"stability": 0.7, "style": 0.7}  # Balanced
   ```

## Testing & Validation

1. **Voice Tests**
   - Test each voice with different emotional tags
   - Verify sound effect integration
   - Check voice consistency across scenes

2. **Performance Metrics**
   - Audio generation time
   - API response reliability
   - Cache hit rates

3. **Quality Checks**
   - Emotional appropriateness
   - Voice clarity and consistency
   - Sound effect timing

## Future Improvements

1. **Advanced Features**
   - Multi-voice dialogues
   - Custom sound effect library
   - Dynamic pacing control

2. **Integration Ideas**
   - Real-time voice adjustment
   - Adaptive emotion detection
   - Interactive voice selection

## Notes

- ElevenLabs V3 handles expressive narration internally through its model
- No need for manual prosody adjustments
- Voice settings can be fine-tuned per scene
- Consider caching frequently used audio segments 