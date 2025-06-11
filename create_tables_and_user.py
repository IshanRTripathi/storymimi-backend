import asyncio
import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_tables_and_user():
    print("Creating tables for StoryMimi...")
    
    # Get Supabase credentials from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return
    
    # Create tables using Supabase REST API
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    # SQL for creating tables
    sql = """
    -- Drop tables if they exist (for clean setup)
    DROP TABLE IF EXISTS scenes;
    DROP TABLE IF EXISTS stories;
    DROP TABLE IF EXISTS users;
    
    -- Create users table with UUID type for user_id
    CREATE TABLE users (
        user_id UUID PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ
    );
    
    -- Create stories table
    CREATE TABLE stories (
        story_id UUID PRIMARY KEY,
        title TEXT NOT NULL,
        prompt TEXT NOT NULL,
        status TEXT NOT NULL,
        user_id UUID REFERENCES users(user_id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ
    );
    
    -- Create scenes table
    CREATE TABLE scenes (
        scene_id UUID PRIMARY KEY,
        story_id UUID REFERENCES stories(story_id),
        sequence INTEGER NOT NULL,
        text TEXT NOT NULL,
        image_url TEXT,
        audio_url TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    try:
        # Use Supabase SQL API to execute the SQL
        # Note: This requires appropriate permissions in your Supabase project
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{supabase_url}/rest/v1/",
                headers=headers,
                params={"q": sql}
            )
            
            if response.status_code >= 400:
                print(f"Error creating tables: {response.status_code} - {response.text}")
                print("Trying alternative method...")
                
                # Try using the SQL editor endpoint
                response = await client.post(
                    f"{supabase_url}/rest/v1/rpc/sql",
                    headers=headers,
                    json={"query": sql}
                )
                
                if response.status_code >= 400:
                    print(f"Error with alternative method: {response.status_code} - {response.text}")
                    print("Please create the tables manually using the Supabase dashboard SQL editor with the SQL provided in this script.")
                    return
            
            print("Tables created successfully!")
            
            # Create a test user
            print("Creating a test user...")
            user_data = {
                "user_id": "00000000-0000-0000-0000-000000000001",
                "email": "test@example.com",
                "username": "testuser"
            }
            
            response = await client.post(
                f"{supabase_url}/rest/v1/users",
                headers=headers,
                json=user_data
            )
            
            if response.status_code >= 400:
                print(f"Error creating test user: {response.status_code} - {response.text}")
            else:
                print("Test user created successfully!")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease create the tables manually using the Supabase dashboard SQL editor with the following SQL:")
        print(sql)

if __name__ == "__main__":
    asyncio.run(create_tables_and_user())