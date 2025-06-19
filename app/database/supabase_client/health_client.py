"""Health check service for Supabase"""
from app.database.supabase_client.base_client import SupabaseBaseClient

class SupabaseHealthService(SupabaseBaseClient):
    """Service for checking Supabase health status"""
    
    async def check_health(self) -> bool:
        """Check if Supabase is healthy by attempting a simple query"""
        try:
            await self.client.table('health_check').select('*').limit(1).execute()
            return True
        except Exception:
            return False 