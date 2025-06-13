import os
import subprocess
import sys
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('startup.log')
    ]
)

logger = logging.getLogger("startup")

# Global variable to track the FastAPI process
fastapi_process = None

def start_fastapi():
    """Start the FastAPI server using uvicorn"""
    logger.info("Starting FastAPI server in simplified mode (without Redis and Celery)...")
    
    # Set environment variable to indicate simplified mode
    os.environ["SIMPLIFIED_MODE"] = "true"
    
    try:
        global fastapi_process
        fastapi_process = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"FastAPI server started with PID: {fastapi_process.pid}")
        
        # Monitor the process output in a non-blocking way
        for line in iter(fastapi_process.stdout.readline, ""):
            logger.info(f"FastAPI: {line.strip()}")
            if "Application startup complete" in line:
                logger.info("FastAPI server is ready!")
                break
        
        return fastapi_process
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {str(e)}", exc_info=True)
        sys.exit(1)

def cleanup():
    """Terminate the FastAPI process on exit"""
    if fastapi_process:
        logger.info(f"Terminating FastAPI server (PID: {fastapi_process.pid})...")
        try:
            fastapi_process.terminate()
            fastapi_process.wait(timeout=5)
            logger.info("FastAPI server terminated successfully.")
        except subprocess.TimeoutExpired:
            logger.warning("FastAPI server did not terminate gracefully, killing...")
            fastapi_process.kill()
        except Exception as e:
            logger.error(f"Error terminating FastAPI server: {e}", exc_info=True)

def signal_handler(sig, frame):
    logger.info("Ctrl+C pressed. Exiting...")
    cleanup()
    sys.exit(0)

def main():
    logger.info("Starting StoryMimi in simplified mode (without Redis and Celery)...")
    
    # Start FastAPI server
    start_fastapi()
    
    logger.info("\nStoryMimi started successfully in simplified mode!")
    logger.info("Press Ctrl+C to stop the server.")
    
    # Register cleanup function to be called on exit
    atexit.register(cleanup)
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if FastAPI process is still running
            if fastapi_process and fastapi_process.poll() is not None:
                exit_code = fastapi_process.poll()
                logger.error(f"FastAPI server exited unexpectedly with code {exit_code}")
                
                # Get the error output
                error_output = fastapi_process.stderr.read()
                logger.error(f"FastAPI server error: {error_output}")
                
                sys.exit(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    import atexit
    main()