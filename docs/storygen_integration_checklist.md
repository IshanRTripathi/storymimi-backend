# Storygen.py Integration Checklist

This document tracks the integration of the advanced prompt and image workflow from `docs/storygen.py` into the main FastAPI + Celery backend.

---

## 1. Service Layer Refactoring
- [x] Create `StoryPromptService` with methods:
  - [x] `generate_structured_story`
  - [x] `generate_visual_profile`
  - [x] `generate_base_style`
  - [x] `generate_scene_moment`
- [x] Refactor prompt templates into this service.
- [x] Ensure all methods are async and use `httpx`.

## 2. AI Service Updates
- [x] Update `AIService` to:
  - [x] Use `StoryPromptService` for prompt-based LLM calls.
  - [x] Add config to switch between mock and real implementations.

## 3. Image Generation Service
- [x] Extend `ImageService` to:
  - [x] Support Together API for image generation.
  - [x] Handle retries, error logging, and return image bytes.

## 4. Story Generation Pipeline
- [x] Refactor `generate_story_async` in `story_generator.py`:
  - [x] Call `generate_structured_story` for story structure.
  - [x] Call `generate_visual_profile` and `generate_base_style` once per story.
  - [x] For each scene:
    - [x] Call `generate_scene_moment`.
    - [x] Compose full image prompt.
    - [x] Call `ImageService` for image.
    - [x] Save all scene data (including image prompt and URL) to DB.

## 5. Configuration
- [x] Add new model names, API keys, and endpoints to `app/config.py` and `.env.example`.
- [x] Allow switching between mock and real services for all LLM/image calls.

## 6. Validation & Error Handling
- [x] Use `Validator` for all new data structures.
- [x] Ensure all LLM/image failures are caught, logged, and update story status.

## 7. Mocking & Testing
- [x] Extend `mock_ai_service.py` to support new prompt types.
- [x] Add/extend unit tests for new service methods and pipeline.

## 8. Documentation
- [ ] Update README and API docs to reflect the new workflow.
- [ ] Add usage examples for the new pipeline.

## 9. Database Integration & Logging (PRIORITY TASKS)
- [x] **(High)** Refactor scene and story creation to support new fields from advanced storygen (child profile, meta, etc.)
- [x] **(High)** Ensure all new fields (visual profile, base style, scene moment, etc.) are persisted in the DB as needed.
- [x] **(High)** Add/extend logging for:
  - [x] All new DB operations (inserts/updates for new fields)
  - [x] Failures or missing data when saving advanced storygen results
  - [x] Timing and performance of batch inserts (for scenes)
- [x] **(Medium)** Add audit trail fields (e.g., `updated_by`, `source` for AI vs. user edits) where relevant.
- [x] **(Medium)** Refactor batch scene insert/update to handle new scene structure and log each operation.
- [x] **(Medium)** Add structured logs for all DB errors, including context (story_id, scene_id, operation type).
- [x] **(Low)** Review and update DB indexes and constraints to support new access patterns (e.g., search by meta fields).
- [ ] **(Low)** Add tests for all new DB integration logic.

---

**Progress:** Mark each item as complete as you implement and test it. 