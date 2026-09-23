"""Configuration management"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Agent Platform - Control Plane"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./agent_platform.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Cognition Plane
    COGNITION_URL: str = "http://localhost:8000"
    
    # Authentication
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"]
    
    class Config:
        # Try to load .env from multiple possible locations
        env_file = ".env"
        case_sensitive = True
        # Make sure environment variables override defaults
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()


settings = get_settings()
