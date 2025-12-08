from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # PUBLIC_INTERFACE
    app_name: str = Field(default="Train Booking Backend", description="Application name")
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=True, description="Enable debug mode")

    # Database
    # PUBLIC_INTERFACE
    DATABASE_URL: str = Field(default="sqlite:///./app.db", description="SQLAlchemy Database URL")

    # Security
    # PUBLIC_INTERFACE
    JWT_SECRET: str = Field(default="CHANGE_ME", description="JWT secret used for signing tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, description="JWT access token expiration in minutes")

    # CORS
    # PUBLIC_INTERFACE
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], description="Allowed CORS origins")

    # Misc
    # PUBLIC_INTERFACE
    API_PREFIX: str = Field(default="/", description="Global API prefix")


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# PUBLIC_INTERFACE
def get_cors_origins() -> List[str]:
    """Return configured CORS origins."""
    return get_settings().CORS_ORIGINS
