import os
import hmac
import hashlib

from dataclasses import dataclass


@dataclass
class Config:
    # Read configuration from environment
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")
    # Token expiry seconds
    TOKEN_MAX_AGE_SECONDS: int = int(os.getenv("TOKEN_MAX_AGE_SECONDS", 300))
    # TTL for cached profiles in seconds (5 minutes)
    USER_PROFILE_CACHE_TTL: int = int(os.getenv("USER_PROFILE_CACHE_TTL", 300))
    QINIU_PREFIX: str = os.getenv("QINIU_PREFIX", "https://cdn.example.local/")


config = Config()


def generate_hmac_signature(user_id: int, timestamp: int) -> str:
    data = f"{user_id}:{timestamp}".encode("utf-8")
    return hmac.new(config.SECRET_KEY.encode("utf-8"), data, hashlib.sha256).hexdigest()
