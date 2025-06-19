# Deployment Cleanup Checklist: StoryMimi Backend

This document tracks the steps to clean up and prepare the repository for production deployment, focusing on FastAPI, Celery, and Redis integration.

---

## 1. Remove Redundant and Dev-Only Files

- [x] Remove `src/main.py` (demo FastAPI app)
- [x] Remove `app/components/` (empty directory)
- [x] Remove `app/services/ai_service_mock_adapter.py` (unused, logic handled elsewhere)
- [x] Remove `app/services/image_generator.py` (unused static function)
- [x] Remove `app/mocks/` (mock AI services and data, dev only)
- [x] Remove `tests/` and `test_create_user.py` (do not include in prod image)
- [x] Remove `start_all.py` and `start_without_redis.py` (dev scripts)
- [x] Remove `logs/` directory and log files (should not be in repo or prod image)
- [x] Remove `docs/` from production image (keep in repo for reference)

## 2. Dockerization & Entrypoints

- [x] Add a `Dockerfile` for the FastAPI/Celery app
- [x] Create `.dockerignore` to exclude unnecessary files from Docker build context
- [x] Ensure `run.py` is used as the FastAPI entrypoint
- [x] Ensure `worker.py` is used as the Celery worker entrypoint
- [x] Update `docker-compose.yml` to run FastAPI and Celery as separate services/containers
- [x] Dockerfile now copies the `static/` directory to fix FastAPI static files error

## 3. Environment & Configuration

- [x] Ensure all secrets and keys are loaded from environment variables (not hardcoded)
- [x] Use `.env.example` as a template for cloud secrets management
- [x] Exclude `.env` from version control (already in .gitignore)

## 4. Static Files & Frontend

- [x] Static files are currently served by backend at `/static`. (Can be changed if frontend is separated in the future.)
- [x] Dockerfile now ensures static files are present in the image

## 5. Logging

- [x] Route logs to stdout/stderr for container/cloud environments (not just files)
- [x] Remove or ignore log files in production

## 6. Health Checks & Monitoring

- [x] `/health` endpoint is present and ready for readiness/liveness probes in cloud
- [ ] Add monitoring/alerting as needed

## 7. Celery Broker/Backend

- [x] Use Redis for local and staging; for production, use managed Redis or RabbitMQ and update `REDIS_URL` in `.env` accordingly
- [x] Update configuration for production broker/backend URLs
- [x] To persist Redis data, use `docker compose stop` and `docker compose start` instead of `down -v` (which deletes volumes)
- [x] Worker retrying Redis connection is normal if Redis is not ready yet; it will connect once Redis is up

## 8. Documentation

- [x] Keep `README.md` and key docs in repo, but exclude large doc folders from production images

## 9. Testing

- [x] Ensure all test scripts are up-to-date and not included in production images

---

## Progress Tracking

- [x] All unnecessary files and folders removed
- [x] Dockerfile created and tested
- [x] .dockerignore created
- [x] Entrypoints and environment variables configured
- [x] Static files and logging reviewed
- [x] Health checks ready for production
- [x] Broker setup for production
- [x] Static files error fixed in Docker
- [x] Redis persistence tip added
- [x] Worker Redis retry behavior documented
- [ ] Monitoring/alerting

---

**Last updated:** 2025-06-19 