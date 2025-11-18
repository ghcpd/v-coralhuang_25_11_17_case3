# fixes — Fixed user module and test environment

Setup:
- Run `bash setup.sh` (or `setup.ps1` on Windows) to create a virtualenv and install dependencies.
- Tests: `bash run_test.sh` or `run_test.bat`.

Docker:
- A Dockerfile is provided to run tests in a container.

Design:
- `fixes/user_module_fixed.py`: corrected endpoints with safe DB, cache, and Celery usage.
- `fixes/config.py`: environment driven config.
- `fixes/db.py`: SQLAlchemy models and helper.
- `fixes/redis_client.py`: Redis wrapper with graceful degradation.
- `fixes/test_user_module.py`: pytest tests.
