"""
Application configuration using Pydantic Settings
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # ============================================================================
    # EXISTING CONFIGURATION
    # ============================================================================

    # Application
    app_name: str = "AI Agent System"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./data/agent.db", description="Database connection URL")

    # Security
    secret_key: str = Field(default="changeme", description="Secret key for JWT and encryption")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.237:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    api_key_groq: Optional[str] = None

    # Ollama (legacy single model)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral:latest"

    # Services
    max_memory_facts: int = 2000
    session_timeout_minutes: int = 30
    max_prompt_length: int = 3500
    max_response_length: int = 2000


    # ============================================================================
    # NEW: MULTI-MODEL AGENT CONFIGURATION
    # ============================================================================

    # Ollama base configuration (for all Ollama models)
    ollama_base_url: str = "http://localhost:11434"

    # Groq cloud API
    groq_api_key: str = ""
    groq_api_base: str = "https://api.groq.com/openai/v1"

    # DeepSeek llama.cpp
    deepseek_model_path: str = "models/deepseek-coder-7b.gguf"
    deepseek_n_ctx: int = 4096
    deepseek_n_threads: int = 4

    # Agent availability flags
    enable_mistral: bool = True
    enable_deepseek: bool = False  # Requires model download
    enable_llama3: bool = True
    enable_groq: bool = False  # Requires API key
    enable_medical: bool = False  # Requires medical model

    # ============================================================================
    # NEW: MEMORISATOR CONFIGURATION
    # ============================================================================

    # Enable/disable automatic fact extraction
    memorisator_enabled: bool = True

    # Model to use for fact extraction (should be gpt-oss for best results)
    memorisator_model: str = "gpt-oss"

    # Fact filtering thresholds
    fact_importance_threshold: float = 0.5  # Only save facts with importance >= this
    fact_confidence_threshold: float = 0.7  # Only save facts with confidence >= this

    # Fact extraction settings
    fact_extraction_temperature: float = 0.3  # Lower = more deterministic
    fact_extraction_max_tokens: int = 2000

    # Background processing
    memorisator_async: bool = True  # Extract facts asynchronously (non-blocking)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    def get_cors_origins(self) -> list:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
