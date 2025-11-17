from flask import Flask

from fixes.cache import CacheClient
from fixes.celery_factory import make_celery_app
from fixes.config import AppConfig
from fixes.db import Database
from fixes.storage import StorageBackend
from fixes.tasks import make_avatar_change_task
from fixes.user_module_fixed import create_user_blueprint


def create_app(config: AppConfig | None = None):
    config = config or AppConfig.from_env()
    database = Database(config.db_url)
    database.create_all()
    cache = CacheClient(redis_url=config.redis_url)
    storage = StorageBackend(config.avatar_base_url)
    celery_app = make_celery_app(config)
    log_avatar_change = make_avatar_change_task(celery_app, database)

    app = Flask(__name__)
    blueprint = create_user_blueprint(
        config=config,
        database=database,
        cache=cache,
        storage=storage,
        log_avatar_change=log_avatar_change,
    )
    app.register_blueprint(blueprint)

    return app, database, cache, celery_app, storage, log_avatar_change
