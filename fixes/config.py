import os
from dataclasses import dataclass

@dataclass
class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER: str = os.environ.get("CELERY_BROKER", "redis://localhost:6379/1")
    CELERY_BACKEND: str = os.environ.get("CELERY_BACKEND", "redis://localhost:6379/2")
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    CELERY_TASK_ALWAYS_EAGER: bool = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "True") == "True"

config = Config()
