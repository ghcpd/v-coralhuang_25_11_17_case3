# Fixed User Module

The `fixes/` directory contains a production-grade implementation of the user profile module, along with a fully reproducible environment (local virtualenv, Docker image, and pytest suite).

## Quick start

```bash
bash fixes/setup.sh
bash fixes/run_test.sh
```

Windows users can execute `fixes\run_test.bat` after running `bash fixes\setup.sh` once.

## Running inside Docker

```bash
bash fixes/run_in_docker.sh
```

The script builds the image defined by `fixes/Dockerfile` and executes the same pytest suite inside the container.

## Module overview

- `fixes/user_module_fixed.py` exposes the `/v1/user/profile` and `/v1/user/avatar` routes via a Flask blueprint.
- `fixes/config.py`, `fixes/extensions.py`, `fixes/redis_utils.py`, `fixes/token_utils.py`, `fixes/storage.py`, and `fixes/tasks.py` provide supporting utilities (configuration loading, SQLAlchemy models, Redis cache access, strict token parsing, deterministic “cloud” uploads, and Celery tasks).
- `fixes/app_factory.py` wires everything together for local usage/tests without touching the original `input.py`.
- Celery runs in eager mode in the default configuration, ensuring deterministic tests while still exercising task registration and database logging.

## API contracts

### Authentication

All routes expect `Authorization: Bearer user:<id>` where `<id>` is a positive integer. Invalid/missing tokens return a `401` response with the structure `{ "error_code": 40100, "msg": "...", "request_url": "/..." }`.

### Success payloads

Every successful request returns `{ "error_code": 0, "msg": "ok", "data": {...} }`. The profile endpoint returns the sanitized user object, while the avatar endpoint returns `{ "avatar": "<url>" }`.

### Error payloads

Errors follow `{ "error_code": int, "msg": str, "request_url": str }` with meaningful HTTP status codes.

## Testing

- `fixes/tests` contains pytest suites that cover cache hits/misses, Redis outages, invalid tokens, avatar uploads, Celery task failures, and database log creation.
- Test logs are written to `fixes/artifacts/test.log` for future inspection. When running `pytest` manually, export `PYTHONPATH=$(pwd)` and `TMPDIR=/tmp/user_module_fixed` to mirror the environment used by `run_test.sh`.

## Configuration

The module reads from environment variables via `fixes/config.py`. Key settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///app.db` | SQLAlchemy database URI |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CACHE_TTL_SECONDS` | `300` | TTL for user profile cache |
| `STORAGE_BUCKET_URL` | `https://cdn.example.invalid` | Prefix used for simulated uploads |
| `CELERY_BROKER_URL` | `memory://` | Celery broker |
| `CELERY_RESULT_BACKEND` | `cache+memory://` | Celery backend |
| `CELERY_TASK_ALWAYS_EAGER` | `1` | Enables eager mode for tests |

The artifacts and upload directories default to `fixes/artifacts/` and are auto-created.

## Integration notes

1. Import `user_bp` from `fixes/user_module_fixed` and register it on your Flask app.
2. Provide a configured SQLAlchemy instance (`fixes/extensions.db.init_app(app)`), Redis factory (`app.config["REDIS_CLIENT_FACTORY"] = lambda: redis.Redis(...)`), and Celery app using `fixes/celery_utils.make_celery`.
3. Register Celery tasks via `fixes.tasks.register_tasks(celery_app)` and store the returned dictionary in `app.config["USER_TASKS"]`.
4. Ensure `fixes/errors.register_error_handlers(app)` is invoked so all responses follow the mandated schema.

See `fixes/app_factory.py` for a complete wiring example.
