#!/bin/bash
# Build and run tests in Docker

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR"

# Build Docker image
echo "Building Docker image..."
docker build -t user_module_tests:latest "$SCRIPT_DIR"

# Run tests in container
echo "Running tests in Docker..."
docker run \
  --rm \
  -e REDIS_HOST=127.0.0.1 \
  -e REDIS_PORT=6379 \
  -e ENV=testing \
  -e CELERY_EAGER=true \
  -e DATABASE_URL=sqlite:///:memory: \
  -v "$SCRIPT_DIR/artifacts:/app/artifacts" \
  user_module_tests:latest

echo "Test run complete!"
exit 0
