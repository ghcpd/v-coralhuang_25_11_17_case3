from dataclasses import dataclass
import os


@dataclass
class AppConfig:
    db_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_url: str
    cache_ttl_seconds: int = 300
    avatar_base_url: str = "https://cdn.example.com/avatars"
    token_prefix: str = "Bearer"
    token_claim_prefix: str = "user:"
    celery_task_always_eager: bool = False
    testing: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
        db_url = os.environ.get("DB_URL", "sqlite:///./user_data.db")
        cache_ttl_seconds = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
        avatar_base_url = os.environ.get("AVATAR_BASE_URL", "https://cdn.example.com/avatars")
        celery_broker_url = os.environ.get("CELERY_BROKER_URL", redis_url)
        celery_result_url = os.environ.get("CELERY_RESULT_URL", redis_url)
        celery_task_always_eager = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "false").lower() in ("1", "true", "yes")
        testing = os.environ.get("FLASK_TESTING", "false").lower() in ("1", "true", "yes")
        return cls(
            db_url=db_url,
            redis_url=redis_url,
            celery_broker_url=celery_broker_url,
            celery_result_url=celery_result_url,
            cache_ttl_seconds=cache_ttl_seconds,
            avatar_base_url=avatar_base_url,
            celery_task_always_eager=celery_task_always_eager,
            testing=testing,
        )
