"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME: str = "GeniAI Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")
    ALLOWED_ORIGINS: List[str] = [
        "https://geniai.sianlk.com",
        "https://app.sianlk.com",
        "https://sianlk.com",
        "http://localhost:3000",
        "http://localhost:8081",
    ]
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    STRIPE_SECRET_KEY: str = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    SENTRY_DSN: str = os.environ.get("SENTRY_DSN", "")
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "production")

    model_config = {"env_file": ".env", "case_sensitive": True}

    def get_allowed_origins(self) -> List[str]:
        """Merge ALLOWED_ORIGINS env-var with defaults at runtime."""
        env_val = os.environ.get("ALLOWED_ORIGINS", "")
        if env_val:
            extra = [o.strip() for o in env_val.split(",") if o.strip()]
            return list(dict.fromkeys(self.ALLOWED_ORIGINS + extra))
        return self.ALLOWED_ORIGINS


settings = Settings()
