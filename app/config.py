from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Service Configuration
    OPENROUTER_API_KEY: str
    TOGETHER_API_KEY: str
    ELEVENLABS_API_KEY: str
    
    # AI Service URLs and Models
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    QWEN_MODEL_NAME: str = "qwen/qwen-2.5-7b-instruct:free"
    TOGETHER_BASE_URL: str = "https://api.together.xyz"
    FLUX_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell"
    
    # Mock Service Configuration
    USE_MOCK_AI_SERVICES: bool = True
    MOCK_DELAY_SECONDS: float = 5.0
    
    # Application Settings
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global settings object
settings = Settings()

def refresh_settings():
    """Refresh settings by reloading from environment variables."""
    global settings
    settings = Settings()