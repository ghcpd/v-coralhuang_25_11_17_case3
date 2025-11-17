# _*_ coding: utf-8 _*_
"""
  Simplified user profile module (buggy example)
  Dependencies: Flask, SQLAlchemy, Redis, Celery, db.py, error.py
"""

import json
import time
from datetime import datetime

from flask import Blueprint, request, current_app
from sqlalchemy import Column, Integer, String, Boolean
from redis import Redis
from celery import Celery

from app.core.db import EntityModel, db
from app.core.error import Success, NotFound, ServerError, APIException

user_bp = Blueprint("user", __name__, url_prefix="/v1/user")

# Global Redis client (buggy: hard-coded config, no connection pool, no error handling)
redis_client = Redis(host="127.0.0.1", port=6379, db=0)

# Celery initialization (buggy: initialized in module with hard-coded broker/backend)
celery_app = Celery(
    "mini_shop_tasks",
    broker="redis://127.0.0.1:6379",
    backend="redis://127.0.0.1:6379"
)


class User(EntityModel):
    """User model (buggy version)."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), unique=True, nullable=False)
    avatar = Column(String(255), comment="avatar url")
    email = Column(String(120), unique=True)
    is_active = Column(Boolean, default=True)
    # Note: there is no `_from` field, but EntityModel.get_url uses self._from

    def to_dict(self):
        """Buggy: blindly copy __dict__, leaking internal attributes."""
        data = self.__dict__.copy()
        # Buggy: only remove _sa_instance_state, other internals are kept
        if "_sa_instance_state" in data:
            del data["_sa_instance_state"]
        return data


def _parse_token(auth_header: str):
    """
    Parse user_id from Authorization header.

    Buggy:
    - No signature/expiration validation
    - Assumes token is just an integer user_id
    """
    if not auth_header:
        raise APIException(code=401, msg="missing authorization header")
    parts = auth_header.split()
    if len(parts) != 2:
        raise APIException(code=401, msg="invalid authorization header format")
    # Buggy: token itself is treated as user_id string
    return int(parts[1])


def _get_user_cache_key(user_id: int) -> str:
    """Build Redis cache key for user profile."""
    return f"user_profile:{user_id}"


@user_bp.route("/profile", methods=["GET"])
def get_profile():
    """Get current user profile (buggy implementation)."""
    try:
        auth = request.headers.get("Authorization")
        user_id = _parse_token(auth)

        cache_key = _get_user_cache_key(user_id)
        cached = redis_client.get(cache_key)

        if cached:
            # Buggy: returning raw bytes, no JSON decoding
            data = cached
            return Success(data=data, error_code=0)

        # Buggy: does not consider soft delete or is_active flag
        user = User.get(id=user_id)
        if not user:
            raise NotFound(msg="user not found")

        # Buggy: json.dumps(model) relies on __dict__, may not be serializable
        user_data = json.dumps(user)

        # Buggy: TTL is given in milliseconds but setex expects seconds
        redis_client.setex(cache_key, 5 * 60 * 1000, user_data)

        return Success(data=user_data, error_code=0)

    except APIException as e:
        # Buggy: returns exception object directly instead of letting global handler process it
        return e
    except Exception:
        # Buggy: swallows original exception details
        return ServerError(msg="internal error"), 500


@user_bp.route("/avatar", methods=["POST"])
def upload_avatar():
    """Upload user avatar (buggy implementation)."""
    auth = request.headers.get("Authorization")
    user_id = _parse_token(auth)

    # Buggy: assumes file key is always "file", no validation
    avatar_file = request.files["file"]

    # Buggy: simulate slow upload in request thread with sleep
    time.sleep(5)

    # Buggy: hard-coded fake CDN prefix, not using configuration
    qiniu_prefix = "http://static.qiniu.fake.com/"
    avatar_url = qiniu_prefix + avatar_file.filename

    # Buggy: no transaction context, partial failures are possible
    user = User.get(id=user_id)
    if not user:
        raise NotFound(msg="user not found when uploading avatar")

    # Buggy: does not check soft delete or is_active
    user.avatar = avatar_url
    db.session.add(user)
    db.session.commit()

    # Buggy: cache structure is inconsistent with profile endpoint
    cache_key = _get_user_cache_key(user_id)
    redis_client.set(cache_key, json.dumps({"id": user.id, "avatar": avatar_url}))

    # Buggy: Celery task uses db.session without proper app context
    log_avatar_change.delay(user_id, avatar_url, datetime.utcnow())

    return Success(data={"avatar": avatar_url}, error_code=1)


@celery_app.task
def log_avatar_change(user_id: int, new_avatar_url: str, changed_at: datetime):
    """
    Record avatar change log (buggy task).

    Bugs:
    - Uses db.session without Flask app context
    - Uses raw SQL with string interpolation (SQL injection risk)
    - No retry or error handling logic
    """
    sql = (
        "INSERT INTO user_avatar_log(user_id, avatar, changed_at) "
        f"VALUES ({user_id}, '{new_avatar_url}', '{changed_at.isoformat()}')"
    )
    db.session.execute(sql)
    db.session.commit()
