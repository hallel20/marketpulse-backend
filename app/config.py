"""
Configuration settings for MarketPulse Commerce API
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(default="", min_length=32)
    ALLOWED_HOSTS: List[str] = Field(default=["*"])
    
    # Database
    DATABASE_URL: str = Field(default="", description="PostgreSQL database URL")
    TEST_DATABASE_URL: str = Field(default="", description="Test database URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379")
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    ALGORITHM: str = Field(default="HS256")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    EMAIL_FROM: str = Field(default="noreply@marketpulse.com")
    
    # Stripe
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    STRIPE_PUBLISHABLE_KEY: str = Field(default="")
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_BUCKET_NAME: str = Field(default="marketpulse-assets")
    AWS_REGION: str = Field(default="us-east-1")
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200")
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    UPLOAD_FOLDER: str = Field(default="uploads")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    MAX_PAGE_SIZE: int = Field(default=100)
    
    # Cache
    CACHE_TTL: int = Field(default=3600)  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()