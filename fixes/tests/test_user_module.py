from __future__ import annotations

import io
from datetime import datetime

import pytest

from fixes.errors import ValidationError
from fixes.extensions import db
from fixes.models import User, UserAvatarLog
from fixes.storage import simulate_avatar_upload
from fixes.token_utils import parse_authorization_header

from fixes.tests.conftest import auth_header_for


def test_get_profile_success(client, user, redis_client):
    response = client.get("/v1/user/profile", headers=auth_header_for(user.id))
    assert response.status_code == 200
    data = response.get_json()
    assert data["error_code"] == 0
    assert data["data"]["id"] == user.id

    cache_key = f"user_profile:{user.id}"
    assert redis_client.exists(cache_key)
    assert redis_client.ttl(cache_key) in (299, 300)


def test_get_profile_uses_cache(client, user, redis_client):
    cache_key = f"user_profile:{user.id}"
    redis_client.set(cache_key, '{"id": 1, "nickname": "cached"}')
    response = client.get("/v1/user/profile", headers=auth_header_for(user.id))
    assert response.status_code == 200
    assert response.get_json()["data"]["nickname"] == "cached"


def test_get_profile_missing_header(client):
    response = client.get("/v1/user/profile")
    assert response.status_code == 401
    body = response.get_json()
    assert body["error_code"] == 40100


def test_get_profile_soft_deleted(client, user):
    with client.application.app_context():
        target = db.session.get(User, user.id)
        target.deleted_at = datetime.utcnow()
        db.session.commit()

    response = client.get("/v1/user/profile", headers=auth_header_for(user.id))
    assert response.status_code == 404


def test_get_profile_inactive(client, user):
    with client.application.app_context():
        target = db.session.get(User, user.id)
        target.is_active = False
        db.session.commit()

    response = client.get("/v1/user/profile", headers=auth_header_for(user.id))
    assert response.status_code == 404


def _avatar_stream(name: str = "avatar.png") -> io.BytesIO:
    stream = io.BytesIO(b"fake-image-bytes")
    stream.name = name
    return stream


def test_upload_avatar_success(client, user, redis_client):
    data = {"file": (_avatar_stream(), "avatar.png")}
    response = client.post(
        "/v1/user/avatar",
        headers=auth_header_for(user.id),
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["avatar"].startswith("https://cdn.test")

    with client.application.app_context():
        updated = db.session.get(User, user.id)
        assert updated.avatar == payload["data"]["avatar"]
        logs = db.session.query(UserAvatarLog).filter_by(user_id=user.id).all()
        assert len(logs) == 1

    cache_key = f"user_profile:{user.id}"
    assert redis_client.exists(cache_key)
    cached = redis_client.get(cache_key)
    assert updated.avatar in cached


def test_upload_avatar_missing_file(client, user):
    response = client.post(
        "/v1/user/avatar",
        headers=auth_header_for(user.id),
        data={},
    )
    assert response.status_code == 400


def test_upload_avatar_inactive_user(client, user):
    with client.application.app_context():
        target = db.session.get(User, user.id)
        target.is_active = False
        db.session.commit()

    response = client.post(
        "/v1/user/avatar",
        headers=auth_header_for(user.id),
        data={"file": (_avatar_stream(), "avatar.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 404


def test_upload_avatar_handles_redis_failure(client, user):
    client.application.config["REDIS_CLIENT_FACTORY"] = lambda: (_ for _ in ()).throw(
        RuntimeError("redis offline")
    )

    response = client.post(
        "/v1/user/avatar",
        headers=auth_header_for(user.id),
        data={"file": (_avatar_stream(), "avatar.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200


def test_upload_avatar_handles_task_failure(client, user):
    class FailingTask:
        def delay(self, *args, **kwargs):
            raise RuntimeError("celery failure")

    client.application.config["USER_TASKS"] = {"record_avatar_change": FailingTask()}

    response = client.post(
        "/v1/user/avatar",
        headers=auth_header_for(user.id),
        data={"file": (_avatar_stream(), "avatar.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200


def test_profile_gracefully_handles_redis_failure(client, user):
    client.application.config["REDIS_CLIENT_FACTORY"] = lambda: (_ for _ in ()).throw(
        RuntimeError("redis offline")
    )
    response = client.get("/v1/user/profile", headers=auth_header_for(user.id))
    assert response.status_code == 200
