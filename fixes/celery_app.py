import os
from celery import Celery

from .config import config


def make_celery(app_name=__name__):
    broker = os.getenv("CELERY_BROKER_URL", config.CELERY_BROKER_URL)
    backend = os.getenv("CELERY_RESULT_BACKEND", config.CELERY_RESULT_BACKEND)
    c = Celery(app_name, broker=broker, backend=backend)
    # Allow eager mode for tests via env or FLASK_ENV=test
    if os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in ("1", "true") or os.getenv("FLASK_ENV") == "test":
        c.conf.task_always_eager = True
        c.conf.task_eager_propagates = True
    return c

celery_app = make_celery()
