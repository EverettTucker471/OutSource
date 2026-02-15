import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # Environment: "local" or "aws"
    ENVIRONMENT: str = "local"

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # Database Configuration
    DATABASE_URL: str = "mysql+pymysql://user:password@db:3306/outsource_db"

    # Database pool settings (tune for RDS in production)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 1800  # seconds; RDS may drop idle connections

    # CORS: comma-separated allowed origins (use "*" to allow all)
    ALLOWED_ORIGINS: str = ""

    # Google Gemini API Configuration
    GEMINI_API_KEY: str

    @property
    def is_aws(self) -> bool:
        return self.ENVIRONMENT.lower() == "aws"

    @property
    def cors_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS:
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables without validation errors


# Singleton instance
settings = Settings()
