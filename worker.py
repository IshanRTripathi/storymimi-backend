from app.workers.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    # This will automatically discover and register tasks from the app.workers module
    celery_app.worker_main(["worker", "--loglevel=info"])