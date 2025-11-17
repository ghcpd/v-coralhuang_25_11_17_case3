from celery import Celery

from fixes.config import AppConfig


def make_celery_app(config: AppConfig) -> Celery:
    celery_app = Celery(
        "user_module_tasks",
        broker=config.celery_broker_url,
        backend=config.celery_result_url,
    )
    celery_app.conf.task_default_queue = "user_module"
    celery_app.conf.task_always_eager = config.celery_task_always_eager
    celery_app.conf.enable_utc = True
    celery_app.conf.worker_prefetch_multiplier = 1
    return celery_app
