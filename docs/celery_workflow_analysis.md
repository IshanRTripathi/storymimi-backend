# Celery Workflow Analysis for StoryMimi Backend

## 1. Overview of Celery Workflow in This Project

### Architecture
- **Celery** is used for background processing of long-running tasks (story generation, media uploads).
- **Broker/Backend**: Redis (see `app/core/celery_app.py`)
- **Task Discovery**: Tasks are auto-discovered from `app.tasks`.
- **Task Example**: `generate_story_task` (see `app/tasks/generate_story_task.py`)
- **Worker Startup**: Via `worker.py` or `start_all.py` (calls `celery_app.worker_main`)
- **Async Handling**: Tasks create their own event loop and run async code using `loop.run_until_complete()`.

### Key Configurations (from `app/core/celery_app.py`)
- `task_serializer`, `result_serializer`: JSON
- `task_time_limit`: 1 hour
- `worker_max_tasks_per_child`: 200
- `task_track_started`: True
- `broker_connection_retry_on_startup`: True
- `task_routes`: All tasks routed to `storymimi` queue

## 2. Identified Potential Issues

### A. Async Event Loop Management
- **Pattern Used**: Each task creates a new event loop (`asyncio.new_event_loop()`) and sets it as current.
- **Potential Issues**:
  - [Celery Issue #3884](https://github.com/celery/celery/issues/3884): Celery does not natively support async tasks; manual event loop management is required.
  - [Celery Discussion #9058](https://github.com/celery/celery/discussions/9058): Creating a new event loop per task can cause resource leaks, thread contention, and issues with DB connection pools (esp. with SQLAlchemy or async DBs).
  - If a task is run in a thread/process where an event loop is already running, using `asyncio.run()` or `loop.run_until_complete()` can raise `RuntimeError`.
  - If event loops are not properly closed, memory leaks or zombie threads may occur.

### B. Task Reliability and Idempotency
- **Pattern Used**: Tasks update DB status to `PROCESSING`/`FAILED`/`COMPLETED`.
- **Potential Issues**:
  - If a worker crashes after starting a task but before completion, the task may be lost or left in an inconsistent state unless `acks_late` and `prefetch_multiplier` are set correctly ([Celery Best Practices](https://gist.github.com/fjsj/da41321ac96cf28a96235cb20e7236f6)).
  - Tasks must be idempotent to safely retry on failure.

### C. Resource Management
- **Pattern Used**: `worker_max_tasks_per_child` is set to 200.
- **Potential Issues**:
  - If tasks leak memory (e.g., due to large AI responses or unclosed resources), workers may become bloated. Restarting after 200 tasks helps, but may not be enough for very large or leaky tasks ([Celery Optimizing Guide](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)).

### D. Error Handling
- **Pattern Used**: Errors are logged and DB status is updated.
- **Potential Issues**:
  - If exceptions are not caught at all levels, tasks may be marked as failed but resources (event loops, DB connections) may not be cleaned up.
  - If the result backend is not configured or is inconsistent, task results may be lost ([Celery Docs](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#keeping-results)).

### E. Broker/Backend Reliability
- **Pattern Used**: Redis for both broker and backend.
- **Potential Issues**:
  - Redis is susceptible to data loss on abrupt shutdown ([Celery Docs](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#choosing-a-broker)).
  - If Redis is unavailable, tasks will not be processed or results will be lost.

## 3. Mitigation Strategies

### A. Async Event Loop Management
- **Best Practice**: Use a single event loop per worker process, or use a helper to run all async code in a dedicated thread/event loop ([GitHub Discussion #9058](https://github.com/celery/celery/discussions/9058)).
- **Mitigation**:
  - Consider using a helper like `asyncio.run_coroutine_threadsafe` with a dedicated event loop thread (see [example](https://github.com/celery/celery/discussions/9058)).
  - Always close event loops after use.
  - Avoid `asyncio.run()` inside Celery tasks; prefer `run_until_complete` on a dedicated loop.

### B. Task Reliability
- **Best Practice**: Set `task_acks_late = True` and `worker_prefetch_multiplier = 1` ([Celery Reliability Gist](https://gist.github.com/fjsj/da41321ac96cf28a96235cb20e7236f6)).
- **Mitigation**:
  - Ensure all tasks are idempotent.
  - Use late acknowledgments to avoid losing tasks on worker crash.
  - Monitor queue lengths and worker health.

### C. Resource Management
- **Best Practice**: Monitor memory usage and set `worker_max_tasks_per_child` and `worker_max_memory_per_child` appropriately ([Celery Optimizing Guide](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)).
- **Mitigation**:
  - Profile memory usage of tasks.
  - Lower `worker_max_tasks_per_child` if memory leaks are observed.

### D. Error Handling
- **Best Practice**: Catch all exceptions, log them, and ensure cleanup of resources (event loops, DB connections).
- **Mitigation**:
  - Use `finally` blocks to close event loops and DB connections.
  - Ensure result backend is always configured and available.

### E. Broker/Backend Reliability
- **Best Practice**: Prefer RabbitMQ for broker in production for higher reliability ([Celery Docs](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html#choosing-a-broker)).
- **Mitigation**:
  - Use Redis only if data loss is acceptable.
  - Monitor broker health and set up alerts for downtime.

## 4. Best Practices for Async in Celery
- Do not use `asyncio.run()` inside Celery tasks; use a dedicated event loop per worker or thread.
- Always await coroutines; never leave them unawaited ([Asyncio Best Practices](https://shanechang.com/p/python-asyncio-best-practices-pitfalls/)).
- Use `run_in_executor()` to call sync code from async, and vice versa.
- Ensure all resources (event loops, DB connections) are cleaned up after task completion or failure.
- Make tasks idempotent and handle retries gracefully.
- Set timeouts for all I/O operations inside tasks.

## 5. References
- [Celery Official Docs: First Steps](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html)
- [Celery Official Docs: Optimizing](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)
- [Celery GitHub Discussion #9058: Async Event Loop](https://github.com/celery/celery/discussions/9058)
- [Celery GitHub Issue #3884: Asyncio Tasks](https://github.com/celery/celery/issues/3884)
- [Celery Reliability Best Practices Gist](https://gist.github.com/fjsj/da41321ac96cf28a96235cb20e7236f6)
- [Asyncio Best Practices and Pitfalls](https://shanechang.com/p/python-asyncio-best-practices-pitfalls/)
- [Flask Docs: Celery Background Tasks](https://flask.palletsprojects.com/en/stable/patterns/celery/) 