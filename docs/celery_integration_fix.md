# Supabase Storage Integration: Async Fixes and Best Practices for FastAPI + Celery

This document explains how to correctly integrate Supabase Storage in an asynchronous FastAPI application with Celery support, resolving common issues with event loop management, coroutine handling, and data validation.

---

## ✅ Key Design Principles (Based on Supabase Docs)

### 1. **Supabase Storage SDK is Sync-Only**

* The Supabase Python SDK (`supabase-py`) provides a **synchronous** API.
* Do not try to `await` or run storage calls using async wrappers directly.
* Docs: [https://supabase.com/docs/reference/python/storage-from-upload](https://supabase.com/docs/reference/python/storage-from-upload)

**✔️ Keep StorageService synchronous.**

### 2. **Async for Database Operations**

* If using an async ORM like `asyncpg` or `SQLAlchemy Async`, keep DB access `async`.
* If using Supabase REST endpoints through `httpx.AsyncClient`, those operations are also async-capable.

**✔️ Keep DB operations async.**

### 3. **Run Sync Storage Calls from Async Code Safely**

Use `run_in_executor()` to safely call sync code from an async function:

```python
image_url = await asyncio.get_event_loop().run_in_executor(
    None,  # Use default executor (thread pool)
    self.storage_service.upload_image,
    story.id,
    i,
    image_bytes
)
```

---

## ❌ Common Runtime Errors & Fixes

### 1. `RuntimeError: Cannot run the event loop while another loop is running`

* Occurs when using `asyncio.run()` inside already-running event loop (like Celery or FastAPI).
* **Fix**: Do not use `asyncio.run()` or `loop.run_until_complete()` inside `async def` functions.
* Use `run_in_executor()` instead.

### 2. `RuntimeWarning: coroutine '...' was never awaited`

* Caused by calling an `async def` function without `await`.
* **Fix**: Always `await` coroutines or convert them to sync functions if they only call sync SDK.

### 3. `ValueError: Missing required field: created_at`

* Happens when async task fails before setting this field.
* **Fix**: Always ensure fields like `created_at`/`updated_at` are assigned before validation or return.

```python
story.created_at = story.created_at or datetime.utcnow()
story.updated_at = datetime.utcnow()
```

---

## ✅ Correct Architecture

| Layer          | Type  | Best Practice                             |
| -------------- | ----- | ----------------------------------------- |
| FastAPI        | Async | Use `async def`                           |
| Celery         | Async | Use `async_=True` or call `asyncio.run()` |
| StoryService   | Async | Async operations with DB and scene gen    |
| StorageService | Sync  | Supabase storage calls (upload, list)     |
| DB Client      | Async | Use SQLAlchemy Async, asyncpg, etc.       |

---

## ✅ Example: StorageService (Sync)

```python
class StorageService:
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.storage = self.client.storage

    def upload_image(self, story_id: str, scene_index: int, image_bytes: bytes) -> str:
        filename = f"scene_{scene_index}_{uuid.uuid4()}.png"
        bucket_name = "story-images"

        try:
            self._ensure_bucket_exists(bucket_name)
            response = self.storage.from_(bucket_name).upload(
                file=image_bytes,
                path=filename,
                file_options={"content-type": "image/png"}
            )
            return self.storage.from_(bucket_name).get_public_url(filename)

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

    def _ensure_bucket_exists(self, bucket_name: str):
        try:
            self.storage.create_bucket(bucket_name)
        except Exception:
            try:
                self.storage.from_(bucket_name).list()
            except:
                raise
```

---

## ✅ Example: StoryService (Async)

```python
class StoryService:
    def __init__(self, db_client, storage_service):
        self.db_client = db_client
        self.storage_service = storage_service

    async def create_new_story(self, request: StoryRequest):
        story = await self.db_client.create_story(
            title=request.title,
            prompt=request.prompt,
            user_id=request.user_id
        )

        scenes = await ai_service.generate_scenes(story.title, story.prompt)
        for i, scene in enumerate(scenes):
            image_bytes = await ai_service.generate_image(scene.text)
            image_url = await asyncio.get_event_loop().run_in_executor(
                None,
                self.storage_service.upload_image,
                story.id,
                i,
                image_bytes
            )
            scene.image_url = image_url

        story.created_at = story.created_at or datetime.utcnow()
        story.updated_at = datetime.utcnow()
        await self.db_client.update_story(story.id, scenes=scenes)

        return story
```

---

## 🧪 Testing Checklist

| ✅ Test Case                        | Description                      |
| ---------------------------------- | -------------------------------- |
| ✅ Upload image from async function | Works via `run_in_executor()`    |
| ✅ Celery task execution            | No nested event loop errors      |
| ✅ All required fields set          | `created_at`, `updated_at`, etc. |
| ✅ FastAPI endpoint                 | End-to-end flow tested           |

---

## 🔗 Supabase References

* [Storage Upload (Python)](https://supabase.com/docs/reference/python/storage-from-upload)
* [Get Public URL](https://supabase.com/docs/reference/python/storage-from-get-public-url)
* [Celery async tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html#coroutine-tasks)
* FastAPI async architecture: [https://fastapi.tiangolo.com/advanced/asyncio/](https://fastapi.tiangolo.com/advanced/asyncio/)

---

## ✅ Summary Fixes

* ✅ Make `StorageService` synchronous
* ✅ Call sync storage using `run_in_executor()`
* ✅ Never call `asyncio.run()` inside Celery or FastAPI
* ✅ Ensure all coroutines are awaited
* ✅ Set required fields like `created_at` before return or validation
