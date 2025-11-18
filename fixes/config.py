"""Configuration helpers for the fixed user module."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


@dataclass(frozen=True)
class AppConfig:
    """Computed application configuration."""

    database_uri: str
    redis_url: str
    cache_ttl_seconds: int
    celery_broker_url: str
    celery_result_backend: str
    celery_task_always_eager: bool
    storage_bucket_url: str
    storage_local_dir: str
    artifacts_dir: str


def _bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    """Load configuration from environment variables with safe defaults."""

    artifacts_dir = Path(
        os.getenv("ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR)
    ).resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    uploads_dir = artifacts_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    if cache_ttl_seconds <= 0:
        cache_ttl_seconds = 300

    storage_bucket_url = os.getenv(
        "STORAGE_BUCKET_URL",
        "https://cdn.example.invalid",
    ).rstrip("/")

    return AppConfig(
        database_uri=os.getenv("DATABASE_URL", "sqlite:///app.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        cache_ttl_seconds=cache_ttl_seconds,
        celery_broker_url=os.getenv("CELERY_BROKER_URL", "memory://"),
        celery_result_backend=os.getenv(
            "CELERY_RESULT_BACKEND", "cache+memory://"
        ),
        celery_task_always_eager=_bool(
            os.getenv("CELERY_TASK_ALWAYS_EAGER", "1"), default=True
        ),
        storage_bucket_url=storage_bucket_url,
        storage_local_dir=str(uploads_dir),
        artifacts_dir=str(artifacts_dir),
    )

