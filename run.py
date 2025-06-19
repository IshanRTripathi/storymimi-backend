import uvicorn
import logging
import sys
from app.config import settings, refresh_settings

# Configure logging for the server startup
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Only log to stdout for container/cloud
    ]
)

logger = logging.getLogger("server_startup")

if __name__ == "__main__":
    try:
        # Ensure we have fresh settings
        refresh_settings()
        
        logger.info(f"Starting FastAPI server on {settings.HOST}:{settings.PORT}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="debug" if settings.DEBUG else "info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)