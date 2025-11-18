import json
from datetime import datetime, timedelta
from flask import Blueprint, request, current_app
from fixes.db import get_session, User, init_db
from fixes.error import Success, NotFound, ServerError
from fixes.redis_client import redis_client
from fixes.token import parse_token
from fixes.celery_app import celery_app

user_bp = Blueprint("user_fixed", __name__, url_prefix="/v1/user")

CACHE_TTL = 5 * 60  # 5 minutes in seconds

# initialize DB for module use (safe to call multiple times)
init_db()

@user_bp.app_errorhandler(Exception)
def _handle_exception(e):
    if hasattr(e, 'to_response'):
        # APIError
        return e.to_response(request.url)
    current_app.logger.exception("Unhandled exception")
    return ServerError().to_response(request.url)

@user_bp.route("/profile", methods=["GET"])
def get_profile():
    try:
        auth = request.headers.get("Authorization")
        user_id = parse_token(auth)

        cache_key = f"user_profile:{user_id}"
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return Success(data=data, error_code=0).to_response()
            except Exception:
                # corrupted cache, ignore and repopulate
                pass

        # ensure safe session usage
        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id, User.deleted_at == None, User.is_active == True).first()
            if not user:
                raise NotFound(msg="user not found")
            user_data = user.to_dict()
            # store in cache (graceful if Redis fails)
            try:
                redis_client.setex(cache_key, CACHE_TTL, json.dumps(user_data))
            except Exception:
                current_app.logger.exception("failed to set cache")
            return Success(data=user_data, error_code=0).to_response()
        finally:
            session.close()

    except Exception as e:
        # APIError handled by handler above. Any other turns into server error
        raise


@user_bp.route("/avatar", methods=["POST"])
def upload_avatar():
    try:
        auth = request.headers.get("Authorization")
        user_id = parse_token(auth)

        if "file" not in request.files:
            return ServerError(msg="missing file").to_response(request.url)
        avatar_file = request.files["file"]
        # validate filename
        filename = avatar_file.filename
        if not filename:
            return ServerError(msg="filename missing").to_response(request.url)

        # Simulate upload to cloud by generating a URL deterministically
        avatar_url = f"https://cdn.example.test/{user_id}/{filename}"

        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id, User.deleted_at == None, User.is_active == True).first()
            if not user:
                raise NotFound(msg="user not found when uploading avatar")

            user.avatar = avatar_url
            session.add(user)
            session.commit()

            cache_key = f"user_profile:{user_id}"
            redis_client.set(cache_key, json.dumps(user.to_dict()))

            # dispatch celery task - in eager mode during tests this runs inline
            try:
                log_avatar_change.delay(user_id, avatar_url, datetime.utcnow())
            except Exception:
                current_app.logger.exception("celery dispatch failed")

            return Success(data={"avatar": avatar_url}, error_code=0).to_response()
        finally:
            session.close()

    except Exception:
        raise


@celery_app.task(bind=True)
def log_avatar_change(self, user_id: int, new_avatar_url: str, changed_at: datetime):
    # Use safe DB access and avoid raw SQL
    session = get_session()
    try:
        # store as a simple Python log (no DB table created in test env)
        current_app.logger.info("Avatar changed: %s %s %s", user_id, new_avatar_url, changed_at.isoformat())
    except Exception:
        current_app.logger.exception("failed to log avatar change")
    finally:
        session.close()
