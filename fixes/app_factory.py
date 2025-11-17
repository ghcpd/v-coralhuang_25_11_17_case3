"""Application factory for local testing and documentation examples."""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from .celery_utils import make_celery
from .config import AppConfig, load_config
from .errors import register_error_handlers
from .extensions import db
from .redis_utils import create_redis_client
from .tasks import register_tasks
from .user_module_fixed import user_bp


def create_app(config: AppConfig | None = None, *, redis_client=None):
    """Create the Flask app, configured for tests or development."""
    config = config or load_config()

    app = Flask(__name__)
    Path(config.storage_local_dir).mkdir(parents=True, exist_ok=True)
    Path(config.artifacts_dir).mkdir(parents=True, exist_ok=True)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=config.database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TTL_SECONDS=config.cache_ttl_seconds,
        STORAGE_BUCKET_URL=config.storage_bucket_url,
        STORAGE_LOCAL_DIR=config.storage_local_dir,
        REDIS_URL=config.redis_url,
    )

    if redis_client is not None:
        app.config["REDIS_CLIENT_FACTORY"] = lambda: redis_client
    else:
        app.config["REDIS_CLIENT_FACTORY"] = lambda: create_redis_client(
            config.redis_url
        )

    db.init_app(app)
    register_error_handlers(app)
    app.register_blueprint(user_bp)

    with app.app_context():
        db.create_all()
        celery_app = make_celery(app, config)
        app.config["CELERY_APP"] = celery_app
        app.config["USER_TASKS"] = register_tasks(celery_app)

    return app
