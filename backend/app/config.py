"""
Configuration module for Hidani Tech AI Job Assistant.
Loads environment variables safely using pydantic-settings / python-dotenv.
"""

import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Base directory for the backend (one level above 'app')
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Allowed CORS origins
    cors_origins: Union[str, List[str]] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
        alias="CORS_ORIGINS"
    )

    # Data paths relative to backend directory
    data_dir: str = Field(default=os.path.join(BACKEND_DIR, "data"), alias="DATA_DIR")
    jobs_file: str = Field(
        default=os.path.join(BACKEND_DIR, "data", "jobs.json"),
        alias="JOBS_FILE"
    )
    applications_file: str = Field(
        default=os.path.join(BACKEND_DIR, "data", "applications.json"),
        alias="APPLICATIONS_FILE"
    )
    sessions_file: str = Field(
        default=os.path.join(BACKEND_DIR, "data", "sessions.json"),
        alias="SESSIONS_FILE"
    )

    # File uploads: Max 5 MB
    max_upload_size_bytes: int = Field(default=5 * 1024 * 1024, alias="MAX_UPLOAD_SIZE_BYTES")

    # LLM Settings
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gemini-1.5-flash", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=15.0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")

    # API Keys
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = {
        "env_file": os.path.join(BACKEND_DIR, ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
