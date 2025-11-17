#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
DEPS_DIR="${DEPS_DIR:-/tmp/fixes_user_module_deps_${USER:-user}}"
ARTIFACTS_DIR="$SCRIPT_DIR/artifacts"
mkdir -p "$ARTIFACTS_DIR"
export PYTHONPATH="$DEPS_DIR:$SCRIPT_DIR/.."
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:---capture=no}"
cd "$SCRIPT_DIR/.."
python -m pytest fixes/tests --junitxml="$ARTIFACTS_DIR/pytest.xml" --log-cli-level=INFO 2>&1 | tee "$ARTIFACTS_DIR/pytest.log"
