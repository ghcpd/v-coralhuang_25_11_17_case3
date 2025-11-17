import os

import fakeredis
import pytest
from flask import Flask

from fixes.cache import CacheClient
from fixes.config import AppConfig
from fixes.db import Database
from fixes.storage import StorageBackend
from fixes.tasks import make_avatar_change_task
from fixes.user_module_fixed import create_user_blueprint
from fixes.celery_factory import make_celery_app


@pytest.fixture
def app_config():
    return AppConfig(
        db_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="memory://",
        celery_result_url="rpc://",
        cache_ttl_seconds=300,
        avatar_base_url="http://cdn.test/avatars/",
        celery_task_always_eager=True,
        testing=True,
    )


@pytest.fixture
def database(app_config):
    database = Database(app_config.db_url)
    database.create_all()
    return database


@pytest.fixture
def cache_client():
    fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
    return CacheClient(client=fake_redis)


@pytest.fixture
def storage_backend(app_config):
    return StorageBackend(app_config.avatar_base_url)


@pytest.fixture
def celery_app(app_config):
    return make_celery_app(app_config)


@pytest.fixture
def log_avatar_change(celery_app, database):
    return make_avatar_change_task(celery_app, database)


@pytest.fixture
def test_app(app_config, database, cache_client, storage_backend, log_avatar_change):
    flask_app = Flask(__name__)
    flask_app.testing = True
    blueprint = create_user_blueprint(
        config=app_config,
        database=database,
        cache=cache_client,
        storage=storage_backend,
        log_avatar_change=log_avatar_change,
    )
    flask_app.register_blueprint(blueprint)
    return flask_app


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", os.getcwd())
