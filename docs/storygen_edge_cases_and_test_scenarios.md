# Story & Scene Generation: Edge Cases and Test Scenarios

This document lists edge cases and scenarios to consider when writing tests for the story and scene generation pipeline, especially given the variability of LLM responses and integration with media generation and storage.

---

## 1. LLM Response Variability
- LLM omits required fields (e.g., scene missing `title`, `image_prompt`, or `text`).
- LLM returns extra/unexpected fields in scene dicts.
- LLM returns empty scenes list or no scenes at all.
- LLM returns scenes with duplicate `sequence` or `scene_id`.
- LLM returns scenes with non-integer `sequence` values.
- LLM returns scene fields as wrong types (e.g., `text` as list, `image_prompt` as int).
- LLM returns scene with empty or whitespace-only `text` or `title`.
- LLM returns scenes with missing or malformed timestamps.
- LLM returns scenes with extremely long or short `text` or `image_prompt`.
- LLM returns scenes with non-unique `scene_id` across different stories.

## 2. Media Generation (Image/Audio)
- Image or audio generation fails (exception, timeout, or returns None/empty bytes).
- Generated media is too small or not valid (e.g., corrupt MP3 or PNG).
- Storage upload fails (network error, permission denied, bucket missing).
- Media URLs returned are not valid URLs or are None.
- Audio/image generation is slow, causing timeouts in the pipeline.
- Media generation returns but with content that does not match the prompt (semantic mismatch).

## 3. Database Integration
- Scene creation fails (DB error, constraint violation, duplicate keys).
- Scene is created but with missing or null required fields.
- Batch insert of scenes fails partway (partial success, rollback needed).
- Scene ordering in DB does not match intended sequence.
- Scene timestamps (`created_at`, `updated_at`) are not set or are inconsistent.
- Scene is not linked to the correct `story_id`.
- Scene is created but not returned by `get_story_scenes`.

## 4. API/Serialization/Validation
- API receives or returns scenes with missing/extra fields.
- Validation fails for scene or story (e.g., due to LLM or DB issues).
- Serialization/deserialization errors (e.g., datetime parsing, UUID parsing).
- Scene or story fails validation but is still saved to DB.
- API returns error but does not update story status to FAILED.

## 5. User/Workflow Edge Cases
- User cancels story generation mid-way (partial data in DB).
- User submits duplicate or conflicting requests (race conditions).
- User requests story with extremely high or low number of scenes.
- User requests story with empty or nonsensical prompt.
- User requests story with prompt that triggers LLM safety filters or content moderation.

## 6. Mock/Real Service Switching
- Mock AI service returns different structure than real AI service.
- Mock media files are missing or corrupt.
- Switching between mock and real services mid-workflow.

## 7. Miscellaneous
- System clock changes during generation (affects timestamps).
- Storage bucket is deleted or renamed during workflow.
- DB schema changes (migration in progress) during generation.
- Network partition or outage during any async step.

---

**For each scenario, tests should verify:**
- Proper error handling and logging.
- Story and scene status updates (e.g., to FAILED on error).
- No partial or corrupt data is left in the DB.
- User-facing API returns clear, actionable error messages.
- All required fields are present and valid in successful cases. 