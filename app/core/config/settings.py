"""
Core application settings and configuration.
This module provides a centralized configuration using Pydantic BaseSettings.
Environment variables can override these settings.
"""

from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    """
    Application settings and configuration.
    All settings can be overridden by environment variables.
    """
    
    # Application Settings
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Database Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Service Configuration
    LLM_BACKEND: Literal["openrouter", "gemini"] = "gemini"
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    QWEN_MODEL_NAME: str = "qwen/qwen-2.5-7b-instruct:free"
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Together AI Configuration
    TOGETHER_API_KEY: str
    TOGETHER_BASE_URL: str = "https://api.together.xyz"
    TOGETHER_API_URL: str = "https://api.together.xyz/v1/images/generations"
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    ELEVENLABS_USE_V3: bool = False
    
    # Image Generation Settings
    IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell-Free"
    IMAGE_WIDTH: int = 1024
    IMAGE_HEIGHT: int = 768
    FLUX_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell"
    
    # Story Generation Models
    STORY_MODEL: str = "deepseek/deepseek-r1-0528:free"
    VISUAL_PROFILE_MODEL: str = "deepseek/deepseek-r1-0528:free"
    BASE_STYLE_MODEL: str = "deepseek/deepseek-r1-0528:free"
    SCENE_MOMENT_MODEL: str = "deepseek/deepseek-r1-0528:free"
    
    # Development & Testing
    USE_MOCK_AI_SERVICES: bool = False
    MOCK_DELAY_SECONDS: float = 5.0
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create a global settings instance
settings = Settings()

def refresh_settings() -> None:
    """
    Refresh settings by reloading from environment variables.
    Useful when environment variables change during runtime.
    """
    global settings
    settings = Settings() 