"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "AI Agent System"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/agent.db",
        description="Database connection URL"
    )
    
    # Security
    secret_key: str = Field(
        default="changeme",
        description="Secret key for JWT and encryption"
    )
    api_key_groq: Optional[str] = None
    
    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral:latest"
    
    # Services
    max_memory_facts: int = 100
    session_timeout_minutes: int = 30
    max_prompt_length: int = 3500
    max_response_length: int = 2000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
