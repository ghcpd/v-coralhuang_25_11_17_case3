#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
ARTIFACTS_DIR="${SCRIPT_DIR}/artifacts"
LOG_FILE="${ARTIFACTS_DIR}/test.log"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Virtual environment missing. Run ${SCRIPT_DIR}/setup.sh first." >&2
  exit 1
fi

mkdir -p "${ARTIFACTS_DIR}"
export TMPDIR="/tmp/user_module_fixed"
export TMP="${TMPDIR}"
export TEMP="${TMPDIR}"
mkdir -p "${TMPDIR}"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"
source "${VENV_DIR}/bin/activate"

set +e
PYTEST_ADDOPTS="--disable-warnings --maxfail=1" pytest -q fixes/tests | tee "${LOG_FILE}"
STATUS=${PIPESTATUS[0]}
set -e

exit ${STATUS}
