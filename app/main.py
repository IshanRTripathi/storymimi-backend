from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import os
import logging
import sys

from app.config import settings
from app.api import stories, users

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

# Suppress Celery timer logs
logging.getLogger('celery.timer').setLevel(logging.WARNING)

# Suppress other Celery debug logs
logging.getLogger('celery').setLevel(logging.INFO)

# Suppress hpack debug logs
logging.getLogger('hpack').setLevel(logging.WARNING)
logging.getLogger('hpack.hpack').setLevel(logging.WARNING)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(
    title="StoryMimi API",
    description="API for generating stories with text, images, and audio using AI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

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
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(stories.router)
app.include_router(users.router)

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
    return {"status": "healthy"}

# Error handler for uncaught exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception(f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )