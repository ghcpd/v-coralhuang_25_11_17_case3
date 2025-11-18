from celery import Celery
from fixes.config import config

def make_celery(app_name=__name__):
    celery = Celery(app_name, broker=config.CELERY_BROKER, backend=config.CELERY_BACKEND)
    # Use eager mode for tests and simple setups
    celery.conf.update(task_always_eager=config.CELERY_TASK_ALWAYS_EAGER)
    return celery

celery_app = make_celery()
