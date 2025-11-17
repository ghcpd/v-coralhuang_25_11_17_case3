"""Celery task registration for the fixed user module."""

from __future__ import annotations

from datetime import datetime

from celery import Celery
from celery.exceptions import Retry
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db
from .models import UserAvatarLog


def register_tasks(celery_app: Celery):
    """Register Celery tasks and return a handle dictionary."""

    @celery_app.task(
        name="user.record_avatar_change",
        bind=True,
        max_retries=3,
        retry_backoff=2,
        retry_jitter=True,
    )
    def record_avatar_change(self, user_id: int, new_avatar_url: str, changed_at: str):
        current_app.logger.info(
            "Recording avatar change for user_id=%s url=%s", user_id, new_avatar_url
        )
        try:
            event = UserAvatarLog(
                user_id=user_id,
                avatar=new_avatar_url,
                changed_at=datetime.fromisoformat(changed_at),
            )
            db.session.add(event)
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            current_app.logger.exception("Failed to record avatar change: %s", exc)
            raise self.retry(exc=exc)

    return {"record_avatar_change": record_avatar_change}

