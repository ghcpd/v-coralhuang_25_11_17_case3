import json
from datetime import datetime
from typing import Callable

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from fixes.cache import CacheClient
from fixes.config import AppConfig
from fixes.db import Database
from fixes.errors import (
    APIException,
    BadRequestError,
    NotFoundError,
    ServerError,
    success_payload,
)
from fixes.models import User
from fixes.storage import StorageBackend
from fixes.token_utils import parse_user_id


def create_user_blueprint(
    *,
    config: AppConfig,
    database: Database,
    cache: CacheClient,
    storage: StorageBackend,
    log_avatar_change: Callable[..., None],
) -> Blueprint:
    user_bp = Blueprint("user", __name__, url_prefix="/v1/user")

    def _cache_key(user_id: int) -> str:
        return f"user_profile:{user_id}"

    @user_bp.errorhandler(APIException)
    def _handle_api_exception(exc: APIException):
        payload = exc.to_payload(request.url)
        return jsonify(payload), exc.status_code

    @user_bp.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        current_app.logger.exception("Unhandled error in user module")
        payload = ServerError().to_payload(request.url)
        return jsonify(payload), ServerError.status_code

    def _success(data: dict | None = None):
        return jsonify(success_payload(data=data or {}))

    def _user_payload(user: User) -> dict:
        return user.to_dict()

    @user_bp.route("/profile", methods=["GET"])
    def get_profile():
        user_id = parse_user_id(
            request.headers.get("Authorization"),
            config.token_prefix,
            config.token_claim_prefix,
        )
        cache_key = _cache_key(user_id)
        cached = cache.get(cache_key)
        if cached:
            try:
                payload = json.loads(cached)
                return _success(payload)
            except json.JSONDecodeError:
                current_app.logger.warning("Corrupted cache for %s", cache_key)
        with database.session_scope(commit=False) as session:
            query = select(User).where(
                User.id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            user = session.scalar(query)
            if user is None:
                raise NotFoundError(msg="user does not exist")
            payload = _user_payload(user)
        try:
            cache.setex(cache_key, config.cache_ttl_seconds, json.dumps(payload))
        except Exception:
            current_app.logger.warning("Failed to refresh cache for %s", cache_key)
        return _success(payload)

    @user_bp.route("/avatar", methods=["POST"])
    def upload_avatar():
        user_id = parse_user_id(
            request.headers.get("Authorization"),
            config.token_prefix,
            config.token_claim_prefix,
        )
        avatar_file = request.files.get("file")
        if avatar_file is None:
            raise BadRequestError(msg="file is required")
        avatar_url = storage.upload(avatar_file)
        cache_key = _cache_key(user_id)
        changed_at = datetime.utcnow().isoformat()
        with database.session_scope(commit=True) as session:
            query = select(User).where(
                User.id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            user = session.scalar(query)
            if user is None:
                raise NotFoundError(msg="user does not exist")
            user.avatar = avatar_url
            session.add(user)
            payload = _user_payload(user)
        try:
            cache.setex(cache_key, config.cache_ttl_seconds, json.dumps(payload))
        except Exception:
            current_app.logger.warning("Failed to refresh cache for %s", cache_key)
        try:
            log_avatar_change.delay(user_id, avatar_url, changed_at)
        except Exception:
            current_app.logger.exception("Celery task failed for avatar change")
        return _success({"avatar": avatar_url})

    return user_bp
