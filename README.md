# StoryMimi Backend

A FastAPI backend application for the StoryMimi project. This backend handles user requests for story generation, orchestrates calls to various AI services (text, image, audio), manages story data in Supabase, and processes long-running tasks asynchronously using Celery and Redis.

## Core Technologies

- **Web Framework:** FastAPI
- **Database & Storage:** Supabase (PostgreSQL and Storage)
- **Asynchronous Task Queue:** Celery with Redis as broker and backend
- **Text Generation LLM:** Qwen-2.5-7B-Instruct (via OpenRouter.ai API)
- **Image Generation:** FLUX.1-schnell (via Together.ai API)
- **Audio Generation:** ElevenLabs API
- **HTTP Client:** `httpx` for asynchronous API calls
- **Data Validation:** Pydantic

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Windows:
```bash
venv\Scripts\activate
```
- On macOS/Linux:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on the `.env.example` file and fill in your API keys and configuration.

## Running the Application

### Option 1: Using the startup script (with Redis)

This option requires Redis to be installed on your system. The script will start Redis, the FastAPI server, and the Celery worker:

```bash
python start_all.py
```

### Option 2: Using Docker for Redis

```bash
# Start Redis using Docker Compose
docker-compose up -d

# Run the FastAPI application
uvicorn app.main:app --reload

# In a separate terminal, start the Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Option 3: Without Redis and Celery (simplified mode)

This option runs only the FastAPI server without background processing. All operations will be performed synchronously:

```bash
python start_without_redis.py
```

## Mock Services

The application includes mock implementations of the AI services to avoid using real API credits during development. To use the mock services:

1. Set `USE_MOCK_AI_SERVICES=True` in your `.env` file (this is the default)
2. Adjust the mock delay with `MOCK_DELAY_SECONDS=5.0` if needed

The mock services return sample data from the `app/mocks/data` directory:
- Text: Sample story texts
- Images: Sample image files
- Audio: Sample audio files

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Project Structure

```
storymimi-backend/
├── app/
│   ├── init.py
│   ├── main.py              # Main FastAPI application entry point
│   ├── config.py            # Pydantic BaseSettings for configuration
│   ├── api/                 # FastAPI routers for API endpoints
│   │   ├── init.py
│   │   ├── stories.py       # Endpoints for story generation, status, retrieval
│   │   └── users.py         # Basic user-related endpoints (e.g., get user stories)
│   ├── mocks/               # Mock implementations of AI services
│   │   ├── init.py
│   │   ├── mock_ai_service.py # Mock implementation of AI service
│   │   └── data/            # Sample data for mock services
│   │       ├── text/        # Sample story texts
│   │       ├── images/      # Sample image files
│   │       └── audio/       # Sample audio files
│   ├── services/            # Business logic and AI/DB interactions
│   │   ├── init.py
│   │   ├── ai_service.py    # Handles all AI API calls (OpenRouter, Together, ElevenLabs)
│   │   ├── ai_service_mock_adapter.py # Factory for switching between real and mock AI services
│   │   └── story_service.py # Orchestrates story creation, calls AI/DB services
│   ├── workers/             # Celery worker definitions
│   │   ├── init.py
│   │   ├── celery_app.py    # Celery application instance and configuration
│   │   └── story_worker.py  # Celery tasks for background story generation
│   ├── database/            # Database client and utilities
│   │   ├── init.py
│   │   └── supabase_client.py # Supabase client for DB and Storage operations
│   └── models/              # Pydantic models for data structures (requests, responses, DB models)
│       ├── init.py
│       ├── story.py         # Models for Story, Scene, StoryRequest, StoryResponse, etc.
│       └── user.py          # Models for User
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables file
├── docker-compose.yml      # Docker Compose for local Redis setup
├── start_all.py            # Script to start all services (Redis, FastAPI, Celery)
├── start_without_redis.py  # Script to start only the FastAPI server
└── README.md               # Project README
```
