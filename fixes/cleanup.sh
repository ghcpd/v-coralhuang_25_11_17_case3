#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

if [[ -d "${VENV_DIR}" ]]; then
  rm -rf "${VENV_DIR}"
  echo "Removed virtual environment at ${VENV_DIR}"
fi

rm -f "${SCRIPT_DIR}/artifacts/test.log"
echo "Cleanup complete."
