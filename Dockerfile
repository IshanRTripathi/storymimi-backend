# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Create a non-root user
RUN useradd -m storymimi

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy only necessary files
COPY app/ ./app/
COPY static/ ./static/
COPY run.py worker.py ./
COPY .env.example ./
COPY README.md ./

# Expose FastAPI port
EXPOSE 8000

# Healthcheck for FastAPI
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1

# Default to non-root user
USER storymimi

# Entrypoint logic (override in docker-compose or k8s):
# For FastAPI: we set the run command here  
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
# For Celery: we dont set the run commands here as the celery workflow is amnaged by cloud run jobs
# CMD ["celery", "-A", "app.core.celery_app:celery_app", "worker", "--loglevel=info"] 