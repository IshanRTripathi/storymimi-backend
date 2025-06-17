# Supabase Setup Instructions

To set up the required tables in your Supabase project, follow these steps:

1. Log in to your Supabase dashboard at https://app.supabase.com/
2. Select your project
3. Go to the SQL Editor (in the left sidebar)
4. Create a new query
5. Paste the following SQL and run it:

```sql
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
    updated_at TIMESTAMPTZ,
    story_metadata JSONB -- New column for LLM structured data
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

-- Insert a test user
INSERT INTO users (user_id, email, username)
VALUES ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'testuser');
```

6. After running the SQL, your database schema will be set up correctly with the tables needed for the application.

## Verifying the Setup

To verify that the tables were created correctly, you can run the following SQL in the SQL Editor:

```sql
SELECT * FROM users;
SELECT * FROM stories;
SELECT * FROM scenes;
```

You should see the test user in the users table, and empty results for the stories and scenes tables.