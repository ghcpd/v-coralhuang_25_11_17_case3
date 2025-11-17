#!/usr/bin/env bash
set -e
# Build image
docker build -t fixes-test -f fixes/Dockerfile .
# Run tests
docker run --rm fixes-test
