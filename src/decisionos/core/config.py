from typing import Literal
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Configuration
    
    Uses Pydantic Settings for strict validation of environment variables.
    Fails fast if critical config is missing.
    """
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

    # Core
    APP_NAME: str = "DecisionOS"
    ENV: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"
    DEMO_MODE: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/decisionos"
    
    # Redis (used for both Cache and Celery)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # LLM Configuration
    USE_LLM: bool = False
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_BASE_URL: str = "https://api.openai.com/v1"

settings = Settings()
