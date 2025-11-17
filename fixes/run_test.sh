#!/usr/bin/env bash
set -euo pipefail
. .venv/Scripts/activate
pytest -q
