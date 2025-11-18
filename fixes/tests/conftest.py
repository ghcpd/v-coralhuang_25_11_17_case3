import os
from pathlib import Path

import fakeredis
import pytest

from fixes.app_factory import create_app
from fixes.config import AppConfig
from fixes.extensions import db
from fixes.models import User


@pytest.fixture
def app_config(tmp_path) -> AppConfig:
    artifacts_dir = tmp_path / "artifacts"
    return AppConfig(
        database_uri=f"sqlite:///{tmp_path/'app.db'}",
        redis_url="redis://localhost:6379/0",
        cache_ttl_seconds=300,
        celery_broker_url="memory://",
        celery_result_backend="cache+memory://",
        celery_task_always_eager=True,
        storage_bucket_url="https://cdn.test",
        storage_local_dir=str(artifacts_dir / "uploads"),
        artifacts_dir=str(artifacts_dir),
    )


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def app(app_config, redis_client):
    application = create_app(app_config, redis_client=redis_client)
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        entity = User(
            nickname="codex",
            email="codex@example.com",
            avatar="https://cdn.test/default.png",
            is_active=True,
        )
        db.session.add(entity)
        db.session.commit()
        return entity


def auth_header_for(user_id: int) -> dict[str, str]:
    return {"Authorization": f"Bearer user:{user_id}"}

