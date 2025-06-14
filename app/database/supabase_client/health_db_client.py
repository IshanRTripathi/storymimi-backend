from typing import Dict, Any

from app.database.supabase_client.base_db_client import SupabaseBaseClient
import logging
import time

logger = logging.getLogger(__name__)

class SupabaseHealthService(SupabaseBaseClient):
    """Service for Supabase health checks"""
    
    async def check_connection(self) -> bool:
        """Check if the connection to Supabase is working
        
        Returns:
            True if connection is working, False otherwise
        """
        start_time = time.time()
        
        logger.info("Checking Supabase connection")
        
        try:
            # Try a simple query to check connection
            self.client.table("users").select("count(*)", count="exact").limit(1).execute()
            
            elapsed = time.time() - start_time
            logger.info(f"Supabase connection check successful in {elapsed:.2f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Supabase connection check failed in {elapsed:.2f}s: {str(e)}", exc_info=True)
            return False
