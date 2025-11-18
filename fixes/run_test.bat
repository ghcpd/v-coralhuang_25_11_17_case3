@echo off
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
if "%1"=="compose" (
  echo Running integration tests with docker-compose...
  powershell -NoProfile -Command "docker compose -f fixes/docker-compose.yml up --build --abort-on-container-exit --exit-code-from pytest; $LASTEXITCODE; docker compose -f fixes/docker-compose.yml down"
) else (
  pytest -q
)
