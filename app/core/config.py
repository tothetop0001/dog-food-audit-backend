"""Application configuration management."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        case_sensitive=True,
        extra="ignore",
    )

    # API Configuration
    api_v1_str: str = Field(default="/api/v1", alias="API_V1_STR", description="API version prefix")
    project_name: str = Field(default="Dog Food API", alias="PROJECT_NAME", description="Project name")
    version: str = Field(default="0.1.0", alias="VERSION", description="API version")
    debug: bool = Field(default=False, alias="DEBUG", description="Debug mode")
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY", description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES", description="Access token expiration time in minutes"
    )

    # Database Configuration
    database_url: str = Field(default="postgresql://postgres:password@localhost:5432/dog_food_db", alias="DATABASE_URL", description="Database connection URL")
    database_url_async: str = Field(default="postgresql+asyncpg://postgres:password@localhost:5432/dog_food_db", alias="DATABASE_URL_ASYNC", description="Async database connection URL")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL", description="Redis URL")

    # Scraping Configuration
    scraping_interval_hours: int = Field(
        default=24, alias="SCRAPING_INTERVAL_HOURS", description="Scraping interval in hours"
    )
    scraping_batch_size: int = Field(
        default=100, alias="SCRAPING_BATCH_SIZE", description="Batch size for scraping operations"
    )
    scraping_delay_seconds: float = Field(
        default=1.0, alias="SCRAPING_DELAY_SECONDS", description="Delay between scraping requests in seconds"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Logging level")
    log_format: str = Field(default="json", alias="LOG_FORMAT", description="Log format (json or text)")

    # External APIs
    external_api_key: Optional[str] = Field(
        default=None, alias="EXTERNAL_API_KEY", description="External API key"
    )
    external_api_base_url: Optional[str] = Field(
        default=None, alias="EXTERNAL_API_BASE_URL", description="External API base URL"
    )

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN", description="Sentry DSN")

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @validator("log_format")
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of {valid_formats}")
        return v.lower()

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.database_url

    @property
    def database_url_async_property(self) -> str:
        """Get asynchronous database URL."""
        return self.database_url_async


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
