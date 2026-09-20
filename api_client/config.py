from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    github_token: str = Field(..., description="GitHub Personal Access Token")
    github_default_user: str = Field(
        default="octocat",
        description="Default GitHub username used when no user is provided",
    )
    github_api_base_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL",
    )
    request_timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
    )
    retry_base_delay: float = Field(
        default=1.0,
        description="Base delay for exponential backoff in seconds",
    )
    rate_limit_threshold: int = Field(
        default=10,
        description="Remaining requests threshold to trigger backoff",
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds",
    )
    cache_db_path: Path = Field(
        default=Path("cache.db"),
        description="Path to SQLite cache database",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
