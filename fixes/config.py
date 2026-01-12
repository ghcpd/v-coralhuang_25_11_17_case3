# _*_ coding: utf-8 _*_
"""
Environment-based configuration management.
Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str
    port: int
    db: int
    connection_pool_size: int = 10
    socket_timeout: int = 5
    socket_keepalive: bool = True

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Load from environment variables."""
        return cls(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            connection_pool_size=int(os.getenv("REDIS_POOL_SIZE", "10")),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
            socket_keepalive=os.getenv("REDIS_KEEPALIVE", "true").lower() == "true"
        )


@dataclass
class CeleryConfig:
    """Celery configuration."""
    broker_url: str
    backend_url: str
    task_always_eager: bool = False
    task_eager_propagates: bool = True
    worker_prefetch_multiplier: int = 1

    @classmethod
    def from_env(cls) -> "CeleryConfig":
        """Load from environment variables."""
        env = os.getenv("ENV", "development").lower()
        return cls(
            broker_url=os.getenv("CELERY_BROKER", "redis://127.0.0.1:6379/1"),
            backend_url=os.getenv("CELERY_BACKEND", "redis://127.0.0.1:6379/2"),
            task_always_eager=env == "testing" or os.getenv("CELERY_EAGER", "false").lower() == "true",
            task_eager_propagates=True,
            worker_prefetch_multiplier=1
        )


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load from environment variables."""
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///:memory:"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        )


@dataclass
class AppConfig:
    """Application configuration."""
    debug: bool = False
    testing: bool = False
    env: str = "development"
    redis: RedisConfig = None
    celery: CeleryConfig = None
    database: DatabaseConfig = None
    cache_ttl_seconds: int = 300  # 5 minutes

    def __post_init__(self):
        """Initialize nested configs if not provided."""
        if self.redis is None:
            self.redis = RedisConfig.from_env()
        if self.celery is None:
            self.celery = CeleryConfig.from_env()
        if self.database is None:
            self.database = DatabaseConfig.from_env()

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load from environment variables."""
        env = os.getenv("ENV", "development").lower()
        return cls(
            debug=env == "development",
            testing=env == "testing",
            env=env,
            redis=RedisConfig.from_env(),
            celery=CeleryConfig.from_env(),
            database=DatabaseConfig.from_env(),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300"))
        )


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig.from_env()
