#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IMAGE_NAME="user-module-fixed:latest"

docker build -t "${IMAGE_NAME}" -f "${SCRIPT_DIR}/Dockerfile" "${REPO_ROOT}"
docker run --rm "${IMAGE_NAME}"
