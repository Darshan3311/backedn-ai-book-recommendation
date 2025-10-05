from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    Using pydantic's BaseSettings for automatic .env file loading
    """
    
    # MongoDB Configuration
    mongo_connection_string: str
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google Gemini Configuration
    gemini_api_key: str
    
    # OpenAI Configuration (optional)
    openai_api_key: Optional[str] = None
    
    # Application Configuration
    app_name: str = "Book Recommendations API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a single settings instance to be used throughout the application
settings = Settings()