import os
import subprocess
import sys
import time
import signal
import atexit

processes = []

def start_redis_docker():
    """Start Redis in Docker"""
    print("Starting Redis in Docker...")
    
    # Check if Redis container is already running
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", "name=redis"],
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        print("Redis container is already running.")
        return None

    try:
        subprocess.run(
            ["docker", "run", "-d", "-p", "6379:6379", "--name", "redis", "redis"],
            check=True
        )
        print("Redis container started successfully.")
    except subprocess.CalledProcessError:
        print("Failed to start Redis Docker container. Make sure Docker is installed and running.")
        sys.exit(1)

def start_fastapi():
    """Start the FastAPI server using uvicorn"""
    print("Starting FastAPI server...")
    fastapi_process = subprocess.Popen(
        [sys.executable, "run.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append((fastapi_process, "FastAPI server"))
    print(f"FastAPI server started with PID: {fastapi_process.pid}")
    time.sleep(2)
    return fastapi_process

def start_celery_worker():
    """Start the Celery worker"""
    print("Starting Celery worker...")
    celery_process = subprocess.Popen(
        [sys.executable, "worker.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append((celery_process, "Celery worker"))
    print(f"Celery worker started with PID: {celery_process.pid}")
    return celery_process

def cleanup():
    """Terminate all processes and stop Redis container on exit"""
    print("\nShutting down all services...")
    for process, name in processes:
        print(f"Terminating {name} (PID: {process.pid})...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"{name} did not terminate gracefully, killing...")
            process.kill()
        except Exception as e:
            print(f"Error terminating {name}: {e}")
    
    print("Stopping Redis Docker container...")
    subprocess.run(["docker", "stop", "redis"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", "redis"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("All services shut down.")

atexit.register(cleanup)

def signal_handler(sig, frame):
    print("\nCtrl+C pressed. Exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    print("Starting all StoryMimi services...")
    
    # Start Redis via Docker
    start_redis_docker()

    # Start FastAPI server
    start_fastapi()

    # Start Celery worker
    start_celery_worker()
    
    print("\nAll services started successfully!")
    print("Press Ctrl+C to stop all services.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
