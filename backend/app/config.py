from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application configuration using Pydantic Settings.
    Automatically loads from environment variables or .env file.
    """
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "TALANTA AI Backend"
    APP_VERSION: str = "1.0.0"
    
    # Database - PostgreSQL
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Database - Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    
    # Cache & Message Broker - Redis
    REDIS_URL: str
    
    # Object Storage - S3/MinIO
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str = "talanta-verifications"
    S3_REGION: str = "us-east-1"
    
    # Security & Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PHONE_HASH_SALT: str
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama, openai, or mock (keyword-based)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "llama3"  # Default model
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1000
    
    # OCR Configuration
    OCR_MODE: str = "paddleocr"  # paddleocr or mock (for MVP)
    
    # Celery Configuration
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Feature Flags
    ENABLE_PII_REDACTION: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_RATE_LIMITING: bool = True
    
    # OTP Settings
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # SMS Configuration (Africa's Talking)
    SMS_API_KEY: Optional[str] = None
    SMS_USERNAME: Optional[str] = None
    SMS_SENDER_ID: str = "TALANTA"
    
    # CORS Settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://talanta.go.ke"
    ]
    
    # Vector Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
