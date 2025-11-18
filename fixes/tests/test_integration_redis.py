import os
import time
import json

import pytest
from fixes.config import generate_hmac_signature, config
from fixes.user_module_fixed import create_app
from fixes.db import get_session, init_db
from fixes.user_module_fixed import User
from fixes.redis_client import get_redis_client


@pytest.fixture(autouse=True)
def setup_env(tmp_path):
    # Use a temp sqlite db for tests
    db_file = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    os.environ["FLASK_ENV"] = "test"
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
    os.environ["SECRET_KEY"] = "test-secret"
    # Do not override REDIS_URL here; docker-compose will set it for integration

    app = create_app()

    # Init DB
    from fixes.db import init_db as _init_db

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


def test_get_profile_integration_real_redis():
    # This test expects REDIS_URL to point at a running redis instance
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        pytest.skip("REDIS_URL not set; skipping integration test")

    app = create_app()
    client = app.test_client()

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0

    # Verify cache exists in real redis
    redis_client = get_redis_client()
    raw = redis_client.get("user_profile:1")
    assert raw is not None

    # TTL should be between 0 and config.CACHE_TTL_SECONDS
    ttl = redis_client.ttl("user_profile:1")
    assert ttl is not None and 0 <= ttl <= config.CACHE_TTL_SECONDS


def test_cache_hit_returns_cached_message():
    redis_client = get_redis_client()
    # Pre-populate cache with known value
    redis_client.setex("user_profile:1", config.CACHE_TTL_SECONDS, json.dumps({"id": 1, "nickname": "cached"}))

    app = create_app()
    client = app.test_client()

    token = make_token(1)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0
    assert body["msg"] == "cached profile"
    assert body["data"]["nickname"] == "cached"
