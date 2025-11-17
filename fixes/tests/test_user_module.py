import os
import json
import time
import tempfile

import pytest
from flask import url_for
import io

from fixes.config import config, generate_hmac_signature
from fixes.user_module_fixed import create_app, log_avatar_change
from fixes.db import get_session, init_db
from fixes.user_module_fixed import User
from fixes.redis_client import get_redis_client


@pytest.fixture(autouse=True)
def setup_env(monkeypatch, tmp_path):
    # Use a temp sqlite db for tests
    db_file = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    os.environ["FLASK_ENV"] = "test"
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
    os.environ["SECRET_KEY"] = "test-secret"
    # configure config again if necessary
    # Create app
    app = create_app()

    # Init DB
    from fixes.db import engine, init_db as _init_db

    _init_db()

    # create a user
    session = get_session()
    u = User(nickname="testuser", email="test@example.com")
    session.add(u)
    session.commit()
    session.close()

    yield


def make_token(user_id: int):
    ts = int(time.time())
    sig = generate_hmac_signature(user_id, ts)
    return f"{user_id}:{ts}:{sig}"


def test_get_profile_no_cache(monkeypatch):
    app = create_app()
    client = app.test_client()

    # monkeypatch redis to isolated fakeredis instance
    import fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("fixes.redis_client.get_redis_client", lambda: fake_redis)

    # create token for user id 1
    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0
    assert body["data"]["id"] == 1

    # verify cache set
    raw = fake_redis.get("user_profile:1")
    assert raw is not None


def test_get_profile_with_cache(monkeypatch):
    app = create_app()
    client = app.test_client()
    import fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    # prepopulate cache
    fake_redis.setex("user_profile:1", 300, json.dumps({"id": 1, "nickname": "cached"}))
    monkeypatch.setattr("fixes.redis_client.get_redis_client", lambda: fake_redis)

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0
    assert body["msg"] == "cached profile"
    assert body["data"]["nickname"] == "cached"


def test_invalid_token_format(monkeypatch):
    app = create_app()
    client = app.test_client()
    token = "not_a_valid_token"
    headers = {"Authorization": f"{token}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 401


def test_upload_avatar_success(monkeypatch):
    app = create_app()
    client = app.test_client()
    import fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("fixes.redis_client.get_redis_client", lambda: fake_redis)

    # token
    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        'file': (io.BytesIO(b"image-data"), 'avatar.png')
    }

    resp = client.post("/v1/user/avatar", data=data, headers=headers, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0
    assert "avatar" in body["data"]

    # verify DB updated
    session = get_session()
    user = session.query(User).filter(User.id == 1).first()
    assert user.avatar is not None
    session.close()


def test_redis_failure(monkeypatch):
    app = create_app()
    client = app.test_client()

    # monkeypatch redis client to throw
    class BrokenClient:
        def get(self, key):
            raise Exception("redis failed")

        def setex(self, key, ttl, value):
            raise Exception("redis failed")

    monkeypatch.setattr("fixes.redis_client.redis_factory.client", lambda: BrokenClient())

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200


def test_celery_task_error_handling(monkeypatch):
    # monkeypatch celery task to raise
    from fixes.user_module_fixed import log_avatar_change
    def failing_delay(*args, **kwargs):
        raise Exception("celery dispatch error")

    monkeypatch.setattr(log_avatar_change, "delay", failing_delay)

    app = create_app()
    client = app.test_client()
    import fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("fixes.redis_client.redis_factory.client", lambda: fake_redis)

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        'file': (io.BytesIO(b"image-data"), 'avatar.png')
    }

    resp = client.post("/v1/user/avatar", data=data, headers=headers, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0


def test_avatar_log_created(monkeypatch):
    # verify task logs avatar change to DB
    app = create_app()
    client = app.test_client()
    import fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("fixes.redis_client.get_redis_client", lambda: fake_redis)

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        'file': (io.BytesIO(b"image-data"), 'avatar.png')
    }

    resp = client.post("/v1/user/avatar", data=data, headers=headers, content_type='multipart/form-data')
    assert resp.status_code == 200

    # Check avatar log created
    from fixes.user_module_fixed import UserAvatarLog
    session = get_session()
    log = session.query(UserAvatarLog).filter(UserAvatarLog.user_id == 1).first()
    assert log is not None
    session.close()


def test_expired_token(monkeypatch):
    app = create_app()
    client = app.test_client()
    # create token with old timestamp
    ts = int(time.time()) - (config.TOKEN_MAX_AGE_SECONDS + 10)
    sig = generate_hmac_signature(1, ts)
    token = f"1:{ts}:{sig}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 401


def test_invalid_signature(monkeypatch):
    app = create_app()
    client = app.test_client()
    ts = int(time.time())
    token = f"1:{ts}:invalidsig"
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 401


def test_soft_delete_behavior(monkeypatch):
    app = create_app()
    client = app.test_client()
    import fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    monkeypatch.setattr("fixes.redis_client.get_redis_client", lambda: fake_redis)

    # mark user as deleted
    session = get_session()
    user = session.query(User).filter(User.id == 1).first()
    user.deleted_at = __import__('datetime').datetime.utcnow()
    session.add(user)
    session.commit()
    session.close()

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 404
