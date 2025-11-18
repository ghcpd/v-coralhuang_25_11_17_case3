#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -r requirements.txt
