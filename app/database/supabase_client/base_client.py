import logging
from supabase import create_client
from app.core.config.settings import settings
from typing import Any, Dict, Optional, Union
import time
import uuid
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class SupabaseBaseClient:
    """Base class for all Supabase service classes"""
    
    def __init__(self):
        """Initialize the Supabase client with proper configuration"""
        logger.info("Initializing Supabase client")
        
        # Validate required settings
        if not settings.SUPABASE_URL:
            logger.error("SUPABASE_URL is not configured")
            raise ValueError("SUPABASE_URL is required for database operations")
        
        if not settings.SUPABASE_KEY:
            logger.error("SUPABASE_KEY is not configured")
            raise ValueError("SUPABASE_KEY is required for database operations")
        
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            self.storage = self.client.storage
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}", exc_info=True)
            raise
    
    def _log_operation(self, operation: str, table: str, data: Any = None, filters: Any = None) -> None:
        """Log database operation details
        
        Args:
            operation: The operation being performed (select, insert, update, delete)
            table: The table being operated on
            data: The data being used in the operation (optional)
            filters: Any filters being applied (optional)
        """
        log_data = {
            "operation": operation,
            "table": table
        }
        
        if data:
            # Limit data logging to avoid excessive log size
            if isinstance(data, dict):
                # Log only keys for dictionaries
                log_data["data_keys"] = list(data.keys())
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                # For list of dicts, log count and keys of first item
                log_data["data_count"] = len(data)
                log_data["data_keys"] = list(data[0].keys()) if data else []
        
        if filters:
            log_data["filters"] = filters
            
        logger.debug(f"Database operation: {log_data}")
