from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and environment configuration"""
    
    # Application
    APP_NAME: str = "VendorScope"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    
    # Crawler Settings
    CRAWLER_USER_AGENT: str = "VendorScope/1.0 (Vendor Risk Analysis Bot)"
    CRAWLER_MAX_PAGES_PER_VENDOR: int = 200
    CRAWLER_RESPECT_ROBOTS_TXT: bool = True
    CRAWLER_RATE_LIMIT_SECONDS: float = 1.0
    
    # Discovery patterns for auto-finding trust pages
    TRUST_PAGE_PATTERNS: list[str] = [
        "/security",
        "/trust",
        "/privacy",
        "/legal",
        "/compliance",
        "/status",
        "/policies",
        "/terms",
        "/gdpr",
        "/soc2",
        "/hipaa",
        "/certifications",
    ]
    
    # RAG Settings
    EMBEDDING_DIMENSION: int = 1536  # text-embedding-3-small
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    
    # Refresh intervals (in days)
    VENDOR_REFRESH_INTERVAL: int = 30
    CRITICAL_VENDOR_REFRESH_INTERVAL: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()