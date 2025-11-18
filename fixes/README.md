# Fixed User Module

This folder contains a corrected and production-ready implementation of the buggy `input.py`.

Features:
- Proper token validation (HMAC-signed, timestamped tokens)
- Redis client factory with connection pool and graceful fallback
- SQLAlchemy-based safe DB transactions
- Celery factory with eager mode for tests
- Structured error handling and logging
- Tests using pytest and fakeredis

Setup (Unix):
1. cd fixes
2. ./setup.sh
3. ./run_test.sh

Setup (Windows):
1. cd fixes
2. run .\run_test.bat

Docker:
- ./run_in_docker.sh will build and run tests inside Docker.

Integration (compose):
- To run integration-style tests against a real Redis instance using docker-compose (recommended for CI), run:
  - ./run_in_docker.sh compose
  - This will start a local `redis` service and run all tests inside a container that connects to it.

