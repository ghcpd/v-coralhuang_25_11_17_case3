#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

if [[ -d "${VENV_DIR}" ]]; then
  echo "Virtual environment already exists at ${VENV_DIR}"
else
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
pip install -r "${SCRIPT_DIR}/requirements.txt"

echo "Environment ready. Activate with: source ${VENV_DIR}/bin/activate"
