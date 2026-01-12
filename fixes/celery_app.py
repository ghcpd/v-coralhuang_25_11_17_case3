# _*_ coding: utf-8 _*_
"""
Celery application factory with proper configuration.
"""

import logging
from typing import Optional

from celery import Celery

logger = logging.getLogger(__name__)

_celery_app: Optional[Celery] = None


def create_celery_app(broker_url: str = "redis://127.0.0.1:6379/1",
                      backend_url: str = "redis://127.0.0.1:6379/2",
                      task_always_eager: bool = False,
                      task_eager_propagates: bool = True,
                      worker_prefetch_multiplier: int = 1) -> Celery:
    """
    Create and configure Celery application.
    
    Args:
        broker_url: Message broker URL
        backend_url: Result backend URL
        task_always_eager: Run tasks synchronously (for testing)
        task_eager_propagates: Propagate exceptions in eager mode
        worker_prefetch_multiplier: Prefetch multiplier
        
    Returns:
        Configured Celery app
    """
    app = Celery("mini_shop_tasks")
    
    # Configure with environment-based settings
    app.conf.update(
        broker_url=broker_url,
        result_backend=backend_url,
        task_always_eager=task_always_eager,
        task_eager_propagates=task_eager_propagates,
        worker_prefetch_multiplier=worker_prefetch_multiplier,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    
    global _celery_app
    _celery_app = app
    
    return app


def get_celery_app() -> Optional[Celery]:
    """Get singleton Celery app instance."""
    return _celery_app


def set_celery_app(app: Celery) -> None:
    """Set singleton Celery app instance."""
    global _celery_app
    _celery_app = app
