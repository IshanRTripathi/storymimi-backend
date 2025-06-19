#!/usr/bin/env python3
"""
Test script to verify Redis connection and Celery task processing.
Run this locally or in a container to test the connection.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test direct Redis connection"""
    try:
        import redis
        from app.core.config.settings import settings
        
        logger.info(f"Testing Redis connection to: {settings.REDIS_URL}")
        
        # Parse Redis URL
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Test connection
        redis_client.ping()
        logger.info("✅ Redis connection successful!")
        
        # Test basic operations
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        logger.info(f"✅ Redis read/write test: {value.decode()}")
        
        # Clean up
        redis_client.delete("test_key")
        
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

def test_celery_connection():
    """Test Celery broker connection"""
    try:
        from app.core.celery_app import celery_app
        
        logger.info("Testing Celery broker connection...")
        
        # Test broker connection
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=3)
        
        logger.info("✅ Celery broker connection successful!")
        
        # Test task discovery
        tasks = list(celery_app.tasks.keys())
        logger.info(f"✅ Discovered {len(tasks)} Celery tasks: {tasks}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Celery connection failed: {e}")
        return False

def test_task_dispatch():
    """Test dispatching a simple task"""
    try:
        from app.core.celery_app import celery_app
        
        logger.info("Testing task dispatch...")
        
        # Create a simple test task
        @celery_app.task
        def test_task(message):
            return f"Task executed: {message}"
        
        # Dispatch task
        result = test_task.delay("Hello from test!")
        logger.info(f"✅ Task dispatched with ID: {result.id}")
        
        # Try to get result (with timeout)
        try:
            task_result = result.get(timeout=10)
            logger.info(f"✅ Task completed: {task_result}")
        except Exception as e:
            logger.warning(f"⚠️ Task result not available (worker may not be running): {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Task dispatch failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=== Redis & Celery Connection Test ===")
    logger.info(f"Test started at: {datetime.now()}")
    
    results = []
    
    # Test 1: Redis connection
    logger.info("\n1. Testing Redis connection...")
    results.append(test_redis_connection())
    
    # Test 2: Celery connection
    logger.info("\n2. Testing Celery connection...")
    results.append(test_celery_connection())
    
    # Test 3: Task dispatch
    logger.info("\n3. Testing task dispatch...")
    results.append(test_task_dispatch())
    
    # Summary
    logger.info("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.info(f"✅ All tests passed ({passed}/{total})")
        return 0
    else:
        logger.error(f"❌ Some tests failed ({passed}/{total})")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 