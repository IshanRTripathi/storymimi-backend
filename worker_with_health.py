#!/usr/bin/env python3
"""
Celery worker with HTTP health check endpoint for Cloud Run.
This script runs both a Celery worker and a simple HTTP server for health checks.
"""

import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler"""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "celery-worker"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs to reduce noise
        pass

def run_health_server():
    """Run the health check HTTP server"""
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server starting on port {port}")
    try:
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")

def run_celery_worker():
    """Run the Celery worker"""
    logger.info("Starting Celery worker...")
    try:
        from app.core.celery_app import celery_app
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=2',
            '--max-tasks-per-child=200'
        ])
    except Exception as e:
        logger.error(f"Celery worker error: {e}")
        raise

def main():
    """Main function to run both health server and Celery worker"""
    logger.info("Starting Celery worker with health check server...")
    
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    logger.info("Health check server thread started")
    
    # Give health server a moment to start
    time.sleep(1)
    
    # Run Celery worker in main thread
    run_celery_worker()

if __name__ == '__main__':
    main() 