"""Database utility helpers."""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError

from .errors import ServerError
from .extensions import db


@contextmanager
def session_scope():
    """Provide a transactional scope."""
    try:
        yield db.session
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise ServerError(f"database error: {exc}") from exc

