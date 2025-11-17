CHANGES - Fixed User Module

Major fixes over input.py:
- Configuration is environment-driven via `fixes/config.py` (no hardcoded Redis/Celery)
- Redis client uses a connection pool and supports graceful fallback to fakeredis for tests
- Celery app factory with support for eager mode during tests
- Token parsing uses HMAC signatures and strict validation (timestamp + expiry)
- Proper serialization of models via `to_dict` to avoid leaking internal attributes
- Cache TTL set in SECONDS and consistent cache structure
- DB transactions use SQLAlchemy sessions and safe commit/rollback handling
- Celery task `log_avatar_change` uses ORM insert rather than raw SQL to avoid injection
- Structured error classes in `fixes/errors.py` provide consistent error format
- Tests cover success & failure cases for both endpoints and verify Redis/Celery behavior

Limitations:
- CDN upload is simulated (no network calls) via a configurable prefix.
- The module uses an in-memory or file-based SQLite DB for tests.

How to integrate:
- Register `user_bp` blueprint from `fixes.user_module_fixed` in your Flask application
- Provide `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `SECRET_KEY` through environment

