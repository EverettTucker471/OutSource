import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # Database Configuration (inherited from existing env vars)
    DATABASE_URL: str = "mysql+pymysql://user:password@db:3306/outsource_db"

    # Google Gemini API Configuration
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables without validation errors


# Singleton instance
settings = Settings()
