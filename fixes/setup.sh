#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
DEPS_DIR="${DEPS_DIR:-/tmp/fixes_user_module_deps_${USER:-user}}"
rm -rf "$DEPS_DIR"
VENV_PYTHON=".venv/bin/python"
export TMPDIR="${TMPDIR:-/tmp}"
export TMP="${TMP:-$TMPDIR}"
export TEMP="${TEMP:-$TMPDIR}"
"$VENV_PYTHON" -m pip install --target "$DEPS_DIR" -r requirements.txt
mkdir -p artifacts
