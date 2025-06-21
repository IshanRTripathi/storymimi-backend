-- Drop and recreate users table to match current models
-- Run this in your Supabase SQL Editor

-- First drop the existing table (this will remove all existing users)
DROP TABLE IF EXISTS users CASCADE;

-- Create users table with correct schema for Firebase auth
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,                    -- Firebase user ID (string, not UUID)
    email TEXT NOT NULL UNIQUE,                 -- Email address
    display_name TEXT,                          -- Optional display name
    created_at TIMESTAMPTZ NOT NULL,           -- Creation timestamp
    firebase_uid TEXT NOT NULL,                -- Firebase UID (usually same as user_id)
    profile_source TEXT NOT NULL DEFAULT 'firebase_auth', -- Profile source
    is_active BOOLEAN NOT NULL DEFAULT true,   -- Active status
    updated_at TIMESTAMPTZ,                    -- Last update timestamp
    cover_image_url TEXT,                      -- Optional cover image URL
    metadata JSONB                             -- Optional metadata JSON
);

-- Add indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Add basic email format validation (simple check)
ALTER TABLE users ADD CONSTRAINT email_format_check 
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Add constraint for profile_source
ALTER TABLE users ADD CONSTRAINT profile_source_check 
CHECK (profile_source IN ('firebase_auth', 'manual', 'other'));

-- Update any foreign key references in other tables if needed
-- (You may need to recreate stories table if it references users with UUID) 