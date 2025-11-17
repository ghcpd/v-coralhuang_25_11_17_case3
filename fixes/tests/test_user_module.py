import io
import json
from datetime import datetime
from unittest.mock import MagicMock

from flask import Flask

from fixes.models import AvatarLog, User
from fixes.storage import StorageBackend
from fixes.user_module_fixed import create_user_blueprint
from fixes.config import AppConfig
from fixes.tasks import make_avatar_change_task
from fixes.celery_factory import make_celery_app
from fixes.db import Database
from fixes.cache import CacheClient


def _auth_header(user_id: int) -> dict:
    return {"Authorization": f"Bearer user:{user_id}"}


def _create_user(database: Database, user_id: int = 1, **kwargs) -> User:
    nickname = kwargs.pop("nickname", f"user-{user_id}")
    with database.session_scope(commit=True) as session:
        user = User(id=user_id, nickname=nickname, **kwargs)
        session.add(user)
    return user


def _build_app(
    config: AppConfig,
    database: Database,
    cache: CacheClient,
    storage: StorageBackend,
    log_avatar_change,
) -> Flask:
    app = Flask(__name__)
    blueprint = create_user_blueprint(
        config=config,
        database=database,
        cache=cache,
        storage=storage,
        log_avatar_change=log_avatar_change,
    )
    app.register_blueprint(blueprint)
    app.testing = True
    return app


class _AlwaysFailRedis:
    def get(self, *_args, **_kwargs):
        raise RuntimeError("redis GET failure")

    def setex(self, *_args, **_kwargs):
        raise RuntimeError("redis SET failure")


def test_get_profile_success_populates_cache(client, database, cache_client, app_config):
    _create_user(database, user_id=1, email="test@example.com")
    response = client.get("/v1/user/profile", headers=_auth_header(1))
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["error_code"] == 0
    assert payload["data"]["id"] == 1
    assert cache_client._client.ttl("user_profile:1") > 0


def test_get_profile_missing_authorization(client):
    response = client.get("/v1/user/profile")
    payload = response.get_json()
    assert response.status_code == 401
    assert payload["error_code"] == 1002
    assert "request_url" in payload


def test_get_profile_user_not_found(client):
    response = client.get("/v1/user/profile", headers=_auth_header(999))
    payload = response.get_json()
    assert response.status_code == 404
    assert payload["error_code"] == 1003


def test_get_profile_soft_deleted(database, client):
    _create_user(database, user_id=2, deleted_at=datetime.utcnow())
    response = client.get("/v1/user/profile", headers=_auth_header(2))
    payload = response.get_json()
    assert response.status_code == 404
    assert payload["error_code"] == 1003


def test_avatar_upload_success(database, client, cache_client, app_config, storage_backend):
    _create_user(database, user_id=3)
    data = {"file": (io.BytesIO(b"image"), "avatar.png")}
    response = client.post("/v1/user/avatar", headers=_auth_header(3), data=data, content_type="multipart/form-data")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["data"]["avatar"].startswith("http://cdn.test/avatars/")
    with database.session_scope(commit=False) as session:
        user = session.get(User, 3)
        assert user.avatar == payload["data"]["avatar"]
    cache_value = cache_client._client.get("user_profile:3")
    assert cache_value is not None
    cache_payload = json.loads(cache_value)
    assert cache_payload["avatar"] == payload["data"]["avatar"]
    with database.session_scope(commit=False) as session:
        logs = session.query(AvatarLog).filter_by(user_id=3).all()
        assert len(logs) == 1


def test_avatar_upload_missing_file(client):
    response = client.post("/v1/user/avatar", headers=_auth_header(1))
    payload = response.get_json()
    assert response.status_code == 400
    assert payload["error_code"] == 1001


def test_avatar_upload_handles_celery_failure(
    database,
    cache_client,
    storage_backend,
    app_config,
):
    _create_user(database, user_id=4)
    fake_task = MagicMock()
    fake_task.delay.side_effect = RuntimeError("boom")
    app = _build_app(
        config=app_config,
        database=database,
        cache=cache_client,
        storage=storage_backend,
        log_avatar_change=fake_task,
    )
    client = app.test_client()
    data = {"file": (io.BytesIO(b"image"), "avatar.png")}
    response = client.post("/v1/user/avatar", headers=_auth_header(4), data=data, content_type="multipart/form-data")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["data"]["avatar"].endswith("avatar.png")
    with database.session_scope(commit=False) as session:
        rows = session.query(AvatarLog).filter_by(user_id=4).all()
        assert rows == []


def test_profile_survives_cache_errors(
    database,
    app_config,
    storage_backend,
):
    _create_user(database, user_id=5)
    failing_cache = CacheClient(client=_AlwaysFailRedis())
    celery_app = make_celery_app(app_config)
    log_avatar_change = make_avatar_change_task(celery_app, database)
    app = _build_app(
        config=app_config,
        database=database,
        cache=failing_cache,
        storage=storage_backend,
        log_avatar_change=log_avatar_change,
    )
    client = app.test_client()
    response = client.get("/v1/user/profile", headers=_auth_header(5))
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["id"] == 5
