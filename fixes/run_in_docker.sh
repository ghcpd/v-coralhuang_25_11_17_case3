#!/usr/bin/env bash
set -euo pipefail
docker build -t fixes-test .
docker run --rm fixes-test
