"""Fixed user module providing profile and avatar endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from flask import Blueprint, current_app, request
from redis import Redis
from sqlalchemy import select

from .db_utils import session_scope
from .errors import NotFoundError, ValidationError, success_response
from .models import User
from .redis_utils import (
    create_redis_client,
    get_cached_profile,
    set_cached_profile,
)
from .storage import simulate_avatar_upload
from .token_utils import parse_authorization_header

user_bp = Blueprint("user_fixed", __name__, url_prefix="/v1/user")


def _get_redis_factory() -> Callable[[], Redis]:
    factory = current_app.config.get("REDIS_CLIENT_FACTORY")
    redis_url = current_app.config.get("REDIS_URL")
    if factory:
        return factory
    if redis_url:
        return lambda: create_redis_client(redis_url)
    raise RuntimeError("Redis configuration missing")


def _get_redis_client_or_none() -> Redis | None:
    try:
        factory = _get_redis_factory()
        return factory()
    except Exception:
        current_app.logger.exception("Failed to acquire Redis client")
        return None


def _cache_profile(user_id: int, payload: dict) -> None:
    client = _get_redis_client_or_none()
    if not client:
        return
    ttl = int(current_app.config.get("CACHE_TTL_SECONDS", 300))
    set_cached_profile(client, user_id, payload, ttl)


def _get_profile_from_cache(user_id: int):
    client = _get_redis_client_or_none()
    if not client:
        return None
    return get_cached_profile(client, user_id)


def _serialize_user(user: User) -> dict:
    return user.to_profile_dict()


@user_bp.route("/profile", methods=["GET"])
def get_profile():
    auth_header = request.headers.get("Authorization")
    user_id, _ = parse_authorization_header(auth_header)

    cached = _get_profile_from_cache(user_id)
    if cached:
        return success_response(cached)

    stmt = (
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None), User.is_active.is_(True))
        .limit(1)
    )
    user = db.session.execute(stmt).scalar_one_or_none()
    if not user or user.deleted_at is not None or not user.is_active:
        raise NotFoundError("user not found")

    payload = _serialize_user(user)
    _cache_profile(user_id, payload)
    return success_response(payload)


@user_bp.route("/avatar", methods=["POST"])
def upload_avatar():
    auth_header = request.headers.get("Authorization")
    user_id, _ = parse_authorization_header(auth_header)

    if "file" not in request.files:
        raise ValidationError("missing file field")
    avatar_file = request.files["file"]
    if not avatar_file.filename:
        raise ValidationError("empty filename")

    config = current_app.config
    try:
        avatar_url = simulate_avatar_upload(
            avatar_file,
            user_id=user_id,
            bucket_url=config["STORAGE_BUCKET_URL"],
            storage_dir=config["STORAGE_LOCAL_DIR"],
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    with session_scope() as session:
        stmt = (
            select(User)
            .where(
                User.id == user_id,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
            )
            .with_for_update()
        )
        user = session.execute(stmt).scalar_one_or_none()
        if not user or user.deleted_at is not None or not user.is_active:
            raise NotFoundError("user not found")

        user.avatar = avatar_url
        session.add(user)

        payload = _serialize_user(user)

    _cache_profile(user_id, payload)

    _dispatch_avatar_change_task(user_id, avatar_url)

    return success_response({"avatar": avatar_url})


def _dispatch_avatar_change_task(user_id: int, avatar_url: str) -> None:
    tasks = current_app.config.get("USER_TASKS") or {}
    task = tasks.get("record_avatar_change")
    if not task:
        current_app.logger.warning("avatar change task not registered")
        return

    try:
        task.delay(user_id, avatar_url, datetime.utcnow().isoformat())
    except Exception:
        current_app.logger.exception("Failed to dispatch avatar change task")


# Import placed at bottom to avoid circular import
from .extensions import db  # noqa: E402
