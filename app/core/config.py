from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Code Review + GitHub Repository Analyst"

    DATABASE_URL: str

    MAX_REPO_SIZE_MB: int = Field(default=50)
    MAX_REPO_FILES: int = Field(default=500)
    MAX_SINGLE_FILE_BYTES: int = Field(default=512000)
    CLONE_TIMEOUT_SECONDS: int = Field(default=45)
    PIPELINE_TIMEOUT_SECONDS: int = Field(default=300)
    TEMP_STORAGE_PATH: str = "./storage/temp_repos"

    LLM_PROVIDER: Literal["mock", "gemini"] = "mock"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"


settings = Settings()
