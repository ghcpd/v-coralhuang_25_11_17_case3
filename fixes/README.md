# Fixed User Module

This directory contains a hardened replacement for the buggy `input.py` module and all supporting infrastructure so you can reproduce a safe, backend-ready service locally or inside Docker.

## Key Features
- Flask blueprint exposing `GET /v1/user/profile` and `POST /v1/user/avatar` with strict authorization token parsing, soft-delete enforcement, and consistent JSON responses.
- SQLAlchemy-managed SQLite database with user and audit models plus transactional updates.
- Redis-backed cache with TTL handling and graceful degradation.
- Celery-powered avatar change recording with configurable broker/worker settings and eager mode for tests.
- Simulated storage backend generating deterministic avatar URLs without network calls.

## Setup (one command)
Ensure you are inside the `fixes/` folder and run:
```
./setup.sh
```
This script creates a lightweight `.venv`, downloads `pip` into your user site (if missing), and installs all dependencies under `/tmp/fixes_user_module_deps_${USER:-user}` so builds are fast and isolated. Log directories are created at `fixes/artifacts/`.

## Running tests (one command)
With the virtual environment active (via `./setup.sh`), run:
```
./run_test.sh
```
`run_test.sh` reuses the `/tmp/fixes_user_module_deps_${USER:-user}` cache by putting it on `PYTHONPATH` before executing `pytest`. Test output is captured under `fixes/artifacts/pytest.log` and `fixes/artifacts/pytest.xml` (junit style) for inspection.

## Running in Docker
A Dockerfile is provided so you can reproduce the environment without installing Python locally.
1. Build the image:
   ```
docker build -t user-module-fixed .
```
2. Run the tests inside the container:
   ```
./run_in_docker.sh
```
This script builds the image (if necessary) and runs the test command inside a disposable container.

## Optional Redis stack via Docker Compose
If you prefer an actual Redis instance during development, use the provided `docker-compose.yml`:
```
docker compose up -d redis
```
Then set `REDIS_URL=redis://localhost:6379/0` before running `./run_test.sh` or `./setup.sh` to have the cache point at the live instance.

## Directory overview
- `fixes/user_module_fixed.py`: Blueprint factory with safe caching, authorization, and avatar handling.
- `fixes/app_factory.py`: Helper to wire configuration, DB, cache, storage, and Celery together.
- `fixes/tests/`: Pytest suite exercising success/failure flows, Redis resilience, and Celery eager tasks.
- `fixes/setup.sh`, `run_test.sh`, `run_test.bat`: Environment management scripts.
- `fixes/Dockerfile`, `run_in_docker.sh`, `docker-compose.yml`: Containerized execution.
- `fixes/artifacts/`: Preserved test logs and generated outputs across runs.
- `CHANGES.md`: Summary of fixes and integration guidance.

## Configuration via environment variables
`AppConfig.from_env()` reads the following optional variables with sane defaults:
- `DB_URL` (default: SQLite file `./user_data.db`)
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_URL`
- `CACHE_TTL_SECONDS` (default `300`)
- `AVATAR_BASE_URL` (used by simulated storage)
- `CELERY_TASK_ALWAYS_EAGER` and `FLASK_TESTING`

Override them before running tests or the Docker container for alternate backends (PostgreSQL, real Redis, etc.).
