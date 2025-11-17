#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker build -t fixes-user-module .
docker run --rm fixes-user-module
