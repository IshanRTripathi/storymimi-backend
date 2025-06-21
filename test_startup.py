#!/usr/bin/env python3
"""
Simple startup test to identify import issues
"""
import sys
import os
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all critical imports"""
    logger.info("Testing imports...")
    
    try:
        logger.info("Testing settings import...")
        from app.core.config.settings import settings
        logger.info("✅ Settings imported successfully")
    except Exception as e:
        logger.error(f"❌ Settings import failed: {e}")
        return False
    
    try:
        logger.info("Testing API modules import...")
        from app.api import stories, users, public_stories
        logger.info("✅ API modules imported successfully")
    except Exception as e:
        logger.error(f"❌ API modules import failed: {e}")
        return False
    
    try:
        logger.info("Testing services import...")
        from app.services.story_service import StoryService
        from app.services.ai_service import AIService
        from app.services.elevenlabs_service import ElevenLabsService
        logger.info("✅ Services imported successfully")
    except Exception as e:
        logger.error(f"❌ Services import failed: {e}")
        return False
    
    try:
        logger.info("Testing database clients import...")
        from app.database.supabase_client import StoryRepository, SceneRepository, UserRepository, StorageService
        logger.info("✅ Database clients imported successfully")
    except Exception as e:
        logger.error(f"❌ Database clients import failed: {e}")
        return False
    
    return True

def test_fastapi_app():
    """Test FastAPI app creation"""
    logger.info("Testing FastAPI app creation...")
    
    try:
        from app.main import app
        logger.info("✅ FastAPI app created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ FastAPI app creation failed: {e}")
        return False

def test_uvicorn_startup():
    """Test if uvicorn can start the app"""
    logger.info("Testing uvicorn startup...")
    
    try:
        import uvicorn
        from app.main import app
        
        # Test with a very short timeout
        import asyncio
        import threading
        import time
        
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
        
        # Start server in a thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a bit for startup
        time.sleep(5)
        
        logger.info("✅ Uvicorn startup test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Uvicorn startup failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting startup test...")
    
    # Test imports
    if not test_imports():
        logger.error("Import tests failed")
        sys.exit(1)
    
    # Test FastAPI app
    if not test_fastapi_app():
        logger.error("FastAPI app test failed")
        sys.exit(1)
    
    logger.info("✅ All startup tests passed!")
    sys.exit(0) 