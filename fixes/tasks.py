from datetime import datetime
import logging

from celery import Celery

from fixes.db import Database
from fixes.models import AvatarLog


def make_avatar_change_task(celery_app: Celery, database: Database):
    logger = logging.getLogger(__name__)

    @celery_app.task(
        bind=False,
        name="fixes.tasks.log_avatar_change",
        max_retries=2,
        default_retry_delay=2,
    )
    def log_avatar_change(user_id: int, avatar_url: str, changed_at_iso: str) -> None:
        logger.info("Recording avatar change for user %s", user_id)
        try:
            changed_at = datetime.fromisoformat(changed_at_iso)
        except ValueError:
            changed_at = datetime.utcnow()
        with database.session_scope(commit=True) as session:
            session.add(
                AvatarLog(user_id=user_id, avatar_url=avatar_url, changed_at=changed_at)
            )

    return log_avatar_change
