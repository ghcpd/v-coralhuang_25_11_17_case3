"""Celery factory helpers."""

from __future__ import annotations

from celery import Celery

from .config import AppConfig


def make_celery(flask_app, config: AppConfig) -> Celery:
    """Create a Celery app bound to the provided Flask application."""
    celery_app = Celery(
        flask_app.import_name,
        broker=config.celery_broker_url,
        backend=config.celery_result_backend,
    )
    celery_app.conf.update(
        task_always_eager=config.celery_task_always_eager,
        task_eager_propagates=True,
        timezone="UTC",
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app

