#!/usr/bin/env bash
set -e
# If argument 'compose' is supplied, use docker-compose to run a local redis service
if [ "$1" = "compose" ] || [ "$1" = "integration" ]; then
  echo "Using docker-compose for integration tests..."
  docker compose -f fixes/docker-compose.yml up --build --abort-on-container-exit --exit-code-from pytest
  ec=$?
  docker compose -f fixes/docker-compose.yml down
  exit $ec
fi

# Default: build image and run tests in a container without compose
# Build image
docker build -t fixes-test -f fixes/Dockerfile .
# Run tests
docker run --rm fixes-test
