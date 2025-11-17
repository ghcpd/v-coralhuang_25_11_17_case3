@echo off
setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
for %%i in ("%SCRIPT_DIR%\..") do set REPO_ROOT=%%~fi
set VENV_DIR=%SCRIPT_DIR%\.venv
set LOG_FILE=%SCRIPT_DIR%\artifacts\test.log

if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo Virtual environment missing. Run setup.sh first.
  exit /b 1
)

if not exist "%SCRIPT_DIR%\artifacts" (
  mkdir "%SCRIPT_DIR%\artifacts"
)

set TMPDIR=%SCRIPT_DIR%\artifacts\tmp
set TMP=%TMPDIR%
set TEMP=%TMPDIR%
if not exist "%TMPDIR%" (
  mkdir "%TMPDIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"
set PYTHONPATH=%REPO_ROOT%;%PYTHONPATH%
set PYTEST_ADDOPTS=--disable-warnings --maxfail=1
pytest -q fixes/tests > "%LOG_FILE%" 2>&1
exit /b %errorlevel%
