# StoryMimi Backend

A robust FastAPI backend for the StoryMimi project, orchestrating story generation with LLMs, image, and audio models, and handling asynchronous workflows with Celery and Redis. This document provides a deep-dive into the backend structure, event flows, and integration points for AI services.

---

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [API Design](#api-design)
- [Data Models](#data-models)
- [Event Flows](#event-flows)
  - [Normal (Synchronous) Flow](#normal-synchronous-flow)
  - [Celery (Asynchronous) Workflow](#celery-asynchronous-workflow)
- [Integration with LLM, Image, and Audio Models](#integration-with-llm-image-and-audio-models)
- [Celery Workflow: Best Practices & Issues](#celery-workflow-best-practices--issues)
- [Configuration & Environment](#configuration--environment)
- [Mocking & Local Development](#mocking--local-development)
- [References](#references)

---

## Architecture Overview

- **Framework:** FastAPI (async, OpenAPI/Swagger support)
- **Database:** Supabase (PostgreSQL + Storage)
- **Async Task Queue:** Celery (with Redis broker/backend)
- **AI Services:**
  - LLM: Qwen-2.5-7B-Instruct (OpenRouter.ai)
  - Image: FLUX.1-schnell (Together.ai)
  - Audio: ElevenLabs
- **HTTP Client:** httpx (async)
- **Validation:** Pydantic

---

## Project Structure

```
storymimi-backend/
├── app/
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # Settings (env, API keys, etc.)
│   ├── api/                   # API routers (stories, users)
│   ├── services/              # Business logic, AI, story orchestration
│   ├── tasks/                 # Celery tasks (background jobs)
│   ├── core/                  # Celery app/config
│   ├── database/              # Supabase DB clients (stories, scenes, users)
│   ├── models/                # Pydantic models (Story, Scene, etc.)
│   ├── utils/                 # Validation, JSON conversion, helpers
│   ├── mocks/                 # Mock AI services for dev/testing
│   └── ...
├── static/                    # Static files (for Swagger UI, etc.)
├── docs/                      # Architecture and workflow docs
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # For local Redis
├── start_all.py               # Script: start API, Celery, Redis
├── start_without_redis.py     # Script: run API only (sync mode)
└── README.md                  # This file
```

---

## API Design

- **Swagger UI:** `/docs` (auto-generated)
- **Key Endpoints:**
  - `POST /stories/` — Create a new story (async, triggers Celery)
  - `GET /stories/{story_id}` — Get full story details (with scenes)
  - `GET /stories/{story_id}/status` — Poll story generation status
  - `GET /stories/search/` — Search stories
  - `GET /stories/recent/` — Recent stories
  - `DELETE /stories/{story_id}` — Delete a story
  - `POST /users/` — Create user
  - `GET /users/{user_id}` — Get user info
  - `GET /users/{user_id}/stories` — Get all stories for a user

---

## Data Models

### Story
- `story_id: UUID`
- `title: str`
- `prompt: str`
- `status: str` (`pending`, `processing`, `completed`, `failed`)
- `user_id: UUID`
- `created_at: datetime`
- `updated_at: datetime`

### Scene
- `scene_id: UUID`
- `title: str`
- `text: str`
- `image_prompt: str`
- `image_url: Optional[str]`
- `audio_url: Optional[str]`
- `created_at: datetime`
- `updated_at: datetime`

### StoryRequest
- `title: str`
- `prompt: str`
- `user_id: UUID`
- `style: Optional[str]`
- `num_scenes: Optional[int]`

---

## Event Flows

### Normal (Synchronous) Flow
- Used only in dev mode (`start_without_redis.py`).
- API call triggers story generation and all AI calls synchronously in the request thread.
- Not recommended for production (blocks API worker).

### Celery (Asynchronous) Workflow
- **1. API Call:** `POST /stories/` creates a DB record (status: `pending`), then dispatches a Celery task with the story ID and request data.
- **2. Celery Worker:**
  - Picks up the task (`generate_story_task`), creates an event loop, and runs the async story generation pipeline.
  - **Pipeline:**
    - Updates story status to `processing`.
    - Calls LLM for story text and scene breakdown.
    - For each scene:
      - Calls image model for illustration, uploads to storage.
      - Calls audio model for narration, uploads to storage.
      - Persists scene in DB.
    - Updates story status to `completed` (or `failed` on error).
- **3. API Polling:** Client polls `/stories/{story_id}/status` until `completed` or `failed`.
- **4. Retrieval:** Client fetches full story and scenes via `/stories/{story_id}`.

#### Celery Task Example
```python
@celery_app.task(bind=True, name="story_task.generate")
def generate_story_task(self, story_id, request_dict, user_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    request = StoryRequest(**request_dict)
    result = loop.run_until_complete(generate_story_async(story_id, request, user_id))
    # ...
```

---

## Integration with LLM, Image, and Audio Models

- **LLM (Text):**
  - Qwen-2.5-7B-Instruct via OpenRouter.ai
  - Prompt built in `story_generator.py`, sent via `httpx` async client
  - Returns story title and scenes (JSON)
- **Image Generation:**
  - FLUX.1-schnell via Together.ai
  - Each scene's `image_prompt` sent to Together.ai, returns base64 image, uploaded to storage
- **Audio Generation:**
  - ElevenLabs API
  - Each scene's `text` sent for TTS, returns audio bytes, uploaded to storage
- **Mocking:**
  - Set `USE_MOCK_AI_SERVICES=True` in `.env` to use local mocks (no API credits needed)

---

## Celery Workflow: Best Practices & Issues

- **Async Event Loop:**
  - Each task creates its own event loop (`asyncio.new_event_loop()`), runs async code, and closes the loop.
  - See [Celery Issue #3884](https://github.com/celery/celery/issues/3884) and [Discussion #9058](https://github.com/celery/celery/discussions/9058) for best practices and pitfalls.
- **Idempotency:**
  - Tasks update DB status and are safe to retry.
- **Resource Management:**
  - `worker_max_tasks_per_child` set to 200 to avoid memory leaks.
- **Error Handling:**
  - All exceptions are logged, DB status is updated, and event loops are closed in `finally` blocks.
- **Broker Reliability:**
  - Redis is used for dev; consider RabbitMQ for production if data loss is unacceptable.
- **See:** [`docs/celery_workflow_analysis.md`](docs/celery_workflow_analysis.md) for a full analysis and mitigation strategies.

---

## Configuration & Environment

- All config is managed via `.env` and `app/config.py` (Pydantic `BaseSettings`).
- **Key Variables:**
  - `SUPABASE_URL`, `SUPABASE_KEY`
  - `REDIS_URL`
  - `OPENROUTER_API_KEY`, `TOGETHER_API_KEY`, `ELEVENLABS_API_KEY`
  - `USE_MOCK_AI_SERVICES`, `MOCK_DELAY_SECONDS`

---

## Mocking & Local Development

- **Mock AI Services:**
  - Use `USE_MOCK_AI_SERVICES=True` to avoid real API calls.
  - Mocks return sample data from `app/mocks/data/`.
- **Testing:**
  - Use the provided Postman collection or Swagger UI for API testing.
  - See `TESTING_GUIDE.md` for more.

---

## References
- [Celery Official Docs](https://docs.celeryproject.org/en/stable/)
- [Celery Async Best Practices](https://github.com/celery/celery/discussions/9058)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OpenRouter.ai API](https://openrouter.ai/docs)
- [Together.ai API](https://docs.together.ai/docs)
- [ElevenLabs API](https://docs.elevenlabs.io/)
- [Supabase Docs](https://supabase.com/docs)
- [Celery Workflow Analysis](docs/celery_workflow_analysis.md)
