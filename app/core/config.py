from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # General App Settings
    APP_NAME: str = "Sherify Campaign Manager"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PUBLIC_API_BASE_URL: str = "http://localhost:8000"

    # Database Configuration (Async PostgreSQL with asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sherify"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sherify_test"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CAMPAIGN_BATCH_SIZE: int = 100

    # Bulk CSV Import Configuration
    MAX_IMPORT_FILE_SIZE_MB: int = 15
    IMPORT_BATCH_SIZE: int = 500
    STORAGE_LOCAL_DIR: str = "uploads/imports"

    # Email Provider Configuration ("mock", "ses", "sendgrid", "resend", "mailgun")
    EMAIL_PROVIDER: str = "mock"

    # Webhook Configuration
    WEBHOOK_SIGNING_SECRET: str = "dev-webhook-signing-secret"

    # Security & JWT Foundation
    JWT_SECRET_KEY: str = "dev-insecure-secret-key-replace-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return [str(item) for item in v]
        return v


settings = Settings()
