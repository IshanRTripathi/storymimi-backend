#!/usr/bin/env python3
"""
Enhanced Celery worker with health check server for Cloud Run deployment.
Includes comprehensive fixes for Celery 5.x Redis reconnection bug (GitHub issue #7276).
"""

import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoint"""
    
    def do_GET(self):
        """Handle GET requests to health check endpoint"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "celery-worker",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override to reduce health check noise in logs"""
        # Only log non-health check requests
        if '/health' not in format % args:
            logger.info(format % args)

def run_health_server():
    """Run the health check HTTP server"""
    try:
        logger.info("Health check server starting on port 8080")
        server = HTTPServer(('', 8080), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health check server error: {e}")
        raise

def run_celery_worker():
    """Run the Celery worker"""
    logger.info("Starting Celery worker...")
    try:
        from app.core.celery_app import celery_app
        
        # CRITICAL: Worker options to fix Redis reconnection bug in Celery 5.x
        # --without-mingle and --without-gossip are essential to prevent task consumption freeze
        worker_options = [
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--max-tasks-per-child=1000',
            '--without-mingle',      # CRITICAL: Prevents Redis reconnection bug
            '--without-gossip',      # CRITICAL: Prevents Redis reconnection bug  
            '--without-heartbeat',   # CRITICAL: Prevents heartbeat-related connection issues
            '--pool=prefork'         # Use prefork pool for better reliability
        ]
        
        logger.info(f"Starting Celery worker with Redis reconnection bug fixes: {worker_options}")
        celery_app.worker_main(worker_options)
    except Exception as e:
        logger.error(f"Celery worker error: {e}")
        raise

def main():
    """Main function to start both health server and Celery worker"""
    logger.info("Starting Celery worker with health check server...")
    
    # Start health check server in daemon thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("Health check server thread started")
    
    # Give health server a moment to start
    time.sleep(1)
    
    # Run Celery worker in main thread (required for proper signal handling)
    run_celery_worker()

if __name__ == "__main__":
    main() 