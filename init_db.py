import asyncio
from app.database.supabase_client import SupabaseClient

async def init_database():
    client = SupabaseClient()
    
    print("Initializing database schema...")
    
    try:
        # Create tables using raw SQL
        sql = """
        -- Create users table
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );

        -- Create stories table
        CREATE TABLE IF NOT EXISTS stories (
            story_id UUID PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            status TEXT NOT NULL,
            user_id UUID REFERENCES users(user_id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );

        -- Create scenes table
        CREATE TABLE IF NOT EXISTS scenes (
            scene_id UUID PRIMARY KEY,
            story_id UUID REFERENCES stories(story_id),
            sequence INTEGER NOT NULL,
            text TEXT NOT NULL,
            image_url TEXT,
            audio_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Execute the SQL
        response = client.client.rpc('exec_sql', {'sql': sql}).execute()
        print("Database schema initialized successfully.")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

if __name__ == "__main__":
    asyncio.run(init_database())