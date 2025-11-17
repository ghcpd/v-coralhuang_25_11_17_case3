import json
import time
import re
import io
import hmac
import hashlib

from flask import Blueprint, request, current_app, Flask
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session

from .config import config, generate_hmac_signature
from .errors import Success, NotFound, ServerError, Unauthorized, BadRequest
from .db import EntityModel, init_db, get_session
from .redis_client import get_redis_client
from .celery_app import celery_app


# Blueprint
user_bp = Blueprint("user", __name__, url_prefix="/v1/user")


from sqlalchemy import Column, String


class User(EntityModel):
    __tablename__ = "user"

    nickname = Column(String(50), unique=True, nullable=False)
    avatar = Column(String(255))
    email = Column(String(120), unique=True)


# Avatar log model
class UserAvatarLog(EntityModel):
    __tablename__ = "user_avatar_log"
    from sqlalchemy import Column, Integer, String, DateTime
    user_id = Column(Integer, nullable=False)
    avatar = Column(String(255), nullable=False)
    changed_at = Column(DateTime, nullable=False)


# Token parser
TOKEN_RE = re.compile(r"^(?:Bearer)\s+(?P<token>.+)$", re.I)


def parse_token_strict(auth_header: str):
    if not auth_header:
        raise Unauthorized(msg="missing authorization header")
    m = TOKEN_RE.match(auth_header)
    if not m:
        raise Unauthorized(msg="invalid authorization header format, expected 'Bearer <token>'")
    token = m.group("token")
    # token format: <user_id>:<timestamp>:<hmac>
    parts = token.split(":")
    if len(parts) != 3:
        raise Unauthorized(msg="invalid token format, expected '<user_id>:<timestamp>:<hmac>'")
    user_id_str, ts_str, sig = parts
    if not user_id_str.isdigit():
        raise Unauthorized(msg="invalid user id in token")
    user_id = int(user_id_str)
    try:
        ts = int(ts_str)
    except Exception:
        raise Unauthorized(msg="invalid timestamp in token")
    # expiry check
    if abs(time.time() - ts) > config.TOKEN_MAX_AGE_SECONDS:
        raise Unauthorized(msg="token expired")
    # verify sig
    expected = generate_hmac_signature(user_id, ts)
    if not hmac.compare_digest(expected, sig):
        raise Unauthorized(msg="invalid token signature")
    return user_id


def _get_user_cache_key(user_id: int) -> str:
    return f"user_profile:{user_id}"


@user_bp.route("/profile", methods=["GET"])
def get_profile_flask():
    try:
        auth = request.headers.get("Authorization")
        user_id = parse_token_strict(auth)

        cache_key = _get_user_cache_key(user_id)
        redis = get_redis_client()

        try:
            cached = redis.get(cache_key)
        except Exception:
            cached = None

        if cached:
            try:
                data = json.loads(cached)
            except Exception:
                data = cached.decode() if isinstance(cached, (bytes, bytearray)) else cached
            return Success(data=data, error_code=0, msg="cached profile").to_response()

        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id, User.deleted_at == None, User.is_active == True).first()
            if not user:
                raise NotFound(msg="user not found")
            user_data = user.to_dict()
            # Set cache with TTL
            try:
                redis.setex(cache_key, config.USER_PROFILE_CACHE_TTL, json.dumps(user_data))
            except Exception:
                pass
            return Success(data=user_data, error_code=0, msg="ok").to_response()
        finally:
            session.close()

    except NotFound as e:
        return e.to_response()
    except Unauthorized as e:
        return e.to_response()
    except Exception as e:
        current_app.logger.exception("failed to get profile")
        return ServerError(msg=str(e)).to_response()


@user_bp.route("/avatar", methods=["POST"])
def upload_avatar_flask():
    try:
        auth = request.headers.get("Authorization")
        user_id = parse_token_strict(auth)

        if "file" not in request.files:
            raise BadRequest(msg="missing file")
        avatar_file = request.files["file"]
        if avatar_file.filename == "":
            raise BadRequest(msg="empty filename")

        # Simulate upload to CDN by generating a URL
        avatar_filename = f"{int(time.time())}_{avatar_file.filename}"
        avatar_url = config.QINIU_PREFIX + avatar_filename

        # Update DB with safe transaction
        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id, User.deleted_at == None, User.is_active == True).first()
            if not user:
                raise NotFound(msg="user not found when uploading avatar")
            user.avatar = avatar_url
            session.add(user)
            session.commit()
            # Update Redis cache
            redis = get_redis_client()
            try:
                user_data = user.to_dict()
                redis.setex(_get_user_cache_key(user_id), config.USER_PROFILE_CACHE_TTL, json.dumps(user_data))
            except Exception:
                pass
            # Dispatch async task
            try:
                log_avatar_change.delay(user_id, avatar_url)
            except Exception:
                # If Celery fails, do not break request
                current_app.logger.exception("celery dispatch failed")
            return Success(data={"avatar": avatar_url}, error_code=0, msg="avatar updated").to_response()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    except NotFound as e:
        return e.to_response()
    except Unauthorized as e:
        return e.to_response()
    except BadRequest as e:
        return e.to_response()
    except Exception as e:
        current_app.logger.exception("failed to upload avatar")
        return ServerError(msg=str(e)).to_response()


@celery_app.task(bind=True)
def log_avatar_change(self, user_id: int, new_avatar_url: str):
    session = get_session()
    from datetime import datetime
    try:
        log = UserAvatarLog(user_id=user_id, avatar=new_avatar_url, changed_at=datetime.utcnow())
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
        import logging
        logging.exception("failed to log avatar change")
    finally:
        session.close()


# For tests / app factory

def create_app(config_obj=None):
    app = Flask(__name__)
    cfg = config_obj or config
    app.config.from_object(cfg)

    # Register blueprint and error handlers
    app.register_blueprint(user_bp)

    # Register exception handlers
    from .errors import APIException

    @app.errorhandler(APIException)
    def handle_api_exception(ex: APIException):
        return ex.to_response()

    return app
