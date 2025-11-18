import json
import pytest
from flask import Flask
from fixes.user_module_fixed import user_bp
from fixes.db import init_db, get_session, User
from fixes import redis_client as rc
from fixes.celery_app import celery_app

@pytest.fixture(autouse=True)
def app():
    app = Flask(__name__)
    app.register_blueprint(user_bp)
    # use testing config
    app.config["TESTING"] = True
    init_db()
    yield app

@pytest.fixture(autouse=True)
def clean_db():
    # clear DB between tests
    session = get_session()
    session.query(User).delete()
    session.commit()
    session.close()
    yield

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_profile_success(client):
    # create user
    session = get_session()
    u = User(nickname="tester", email="a@b.com")
    session.add(u)
    session.commit()
    uid = u.id
    session.close()

    # ensure no cache
    rc.redis_client.setex(f"user_profile:{uid}", 1, json.dumps({"id": uid}))

    # once set above, it will be a cache hit
    headers = {"Authorization": f"Bearer {uid}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0
    assert body["data"]["id"] == uid


def test_get_profile_missing_token(client):
    resp = client.get("/v1/user/profile")
    assert resp.status_code == 401


def test_avatar_update_and_cache(client):
    session = get_session()
    u = User(nickname="avatar", email="a@b.com")
    session.add(u)
    session.commit()
    uid = u.id
    session.close()

    data = {"file": (io.BytesIO(b"imgdata"), "pic.png")}
    headers = {"Authorization": f"Bearer {uid}"}
    resp = client.post("/v1/user/avatar", headers=headers, data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0
    assert "avatar" in body["data"]

    # confirm cache updated
    cached = rc.redis_client.get(f"user_profile:{uid}")
    assert cached is not None


def test_redis_failure_graceful(client, monkeypatch):
    # monkeypatch redis to throw on get
    class BadRedis:
        def get(self, key):
            raise RuntimeError("redis down")
        def setex(self, key, seconds, value):
            raise RuntimeError("redis down")
    monkeypatch.setattr(rc, 'redis_client', BadRedis())

    session = get_session()
    u = User(nickname="redisfail", email="c@d.com")
    session.add(u)
    session.commit()
    uid = u.id
    session.close()

    headers = {"Authorization": f"Bearer {uid}"}
    resp = client.get("/v1/user/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["error_code"] == 0


def test_celery_eager_mode(client):
    assert celery_app.conf.task_always_eager in (True, False)
    # In our config we default to True for tests
    assert celery_app.conf.task_always_eager is True

import io
