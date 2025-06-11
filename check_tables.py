import asyncio
from app.database.supabase_client import SupabaseClient

async def check_tables():
    client = SupabaseClient()
    try:
        # Check users table
        response = client.client.table('users').select('count').execute()
        print('Users table exists with', len(response.data), 'records')
        
        # Check stories table
        response = client.client.table('stories').select('count').execute()
        print('Stories table exists with', len(response.data), 'records')
        
        # Check scenes table
        response = client.client.table('scenes').select('count').execute()
        print('Scenes table exists with', len(response.data), 'records')
    except Exception as e:
        print('Error checking tables:', str(e))

if __name__ == "__main__":
    asyncio.run(check_tables())