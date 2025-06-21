from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import os
import logging
import sys

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Only log to stdout for container/cloud
    ]
)

logger = logging.getLogger(__name__)

try:
    from app.core.config.settings import settings, validate_required_settings
    logger.info("Settings imported successfully")
    
    # Validate required settings
    validate_required_settings()
    
except Exception as e:
    logger.error(f"Failed to import settings: {str(e)}", exc_info=True)
    raise

try:
    from app.api import stories, users, public_stories
    logger.info("API modules imported successfully")
except Exception as e:
    logger.error(f"Failed to import API modules: {str(e)}", exc_info=True)
    raise

# Suppress Celery timer logs
logging.getLogger('celery.timer').setLevel(logging.WARNING)

# Suppress other Celery debug logs
logging.getLogger('celery').setLevel(logging.INFO)

# Suppress hpack debug logs
logging.getLogger('hpack').setLevel(logging.WARNING)
logging.getLogger('hpack.hpack').setLevel(logging.WARNING)

# Create the FastAPI application
try:
    app = FastAPI(
        title="StoryMimi API",
        description="API for generating stories with text, images, and audio using AI",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    logger.info("FastAPI app created successfully")
except Exception as e:
    logger.error(f"Failed to create FastAPI app: {str(e)}", exc_info=True)
    raise

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add processing time to response headers"""
    start_time = time.time()
    logger.debug(f"Request started: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.debug(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
        return response
    except Exception as e:
        logger.exception(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}")
        raise

# Mount static files directory
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.warning(f"Failed to mount static files: {str(e)}")

# Include routers
try:
    app.include_router(stories.router)
    app.include_router(users.router)
    app.include_router(public_stories.router)
    logger.info("All routers included successfully")
except Exception as e:
    logger.error(f"Failed to include routers: {str(e)}", exc_info=True)
    raise

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint - redirects to static index.html"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

# Error handler for uncaught exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception(f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

logger.info("FastAPI application setup completed successfully")

# Run the application
if __name__ == "__main__":
    import uvicorn
    try:
        logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)