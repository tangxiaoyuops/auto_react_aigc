"""Configuration management"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Agent Platform - Cognition Plane"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # LLM API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # AIMP Qwen3-5-397B NoThink (OpenAI 兼容接口)
    AIMP_OPENAI_API_BASE: str = "https://aimpapi.midea.com/t-aigc/d-dban-qwen3-5-397b-a17b/v1"
    AIMP_OPENAI_API_KEY: str = ""
    QWEN3_5_MODEL: str = "qwen3-5-397b-a17b"
    QWEN3_5_ENABLE_THINKING: bool = False

    # Default Model
    DEFAULT_MODEL: str = "qwen3-5-397b-a17b"
    
    # Agent settings
    MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300
    
    # Mock 模式：没有配置任何 LLM API Key 时自动启用
    # 此时引擎输出模拟 Trace 事件，保证前端调试链路可跑通
    @property
    def MOCK_MODE(self) -> bool:
        return not (
            self.OPENAI_API_KEY
            or self.ANTHROPIC_API_KEY
            or self.AIMP_OPENAI_API_KEY
        )
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/agent_platform"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()


settings = get_settings()
