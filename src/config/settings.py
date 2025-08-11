"""Application configuration settings."""

from typing import List, Optional
from functools import lru_cache
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # Application Settings
    app_name: str = Field(default="AssignmentScraper", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://scraper:scraper123@localhost:5432/scraper_db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_cache_ttl: int = Field(default=3600, env="REDIS_CACHE_TTL")
    
    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND"
    )
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production", env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Scraping Configuration
    default_timeout: int = Field(default=30, env="DEFAULT_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    delay_between_requests: float = Field(default=1.0, env="DELAY_BETWEEN_REQUESTS")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="USER_AGENT"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Monitoring
    prometheus_port: int = Field(default=8001, env="PROMETHEUS_PORT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    # Browser Configuration
    headless_browser: bool = Field(default=True, env="HEADLESS_BROWSER")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    
    # API Configuration
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        cors_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        return [i.strip() for i in cors_str.split(",") if i.strip()]
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Global settings instance
settings = get_settings() 