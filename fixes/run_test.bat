@echo off
setlocal
cd /d "%~dp0"
IF NOT EXIST .venv\Scripts\activate.bat (
    echo Virtual environment not found. Run setup.bat or setup.sh first.
    exit /b 1
)
call .venv\Scripts\activate.bat
if "%DEPS_DIR%"=="" (
    set "DEPS_DIR=%TEMP%\fixes_user_module_deps_%USERNAME%"
)
set "ARTIFACTS_DIR=%~dp0artifacts"
if not exist "%ARTIFACTS_DIR%" mkdir "%ARTIFACTS_DIR%"
set "ROOT_DIR=%~dp0.."
set "PYTHONPATH=%DEPS_DIR%;%ROOT_DIR%"
if "%PYTEST_ADDOPTS%"=="" (
    set "PYTEST_ADDOPTS=--capture=no"
)
cd /d "%ROOT_DIR%"
python -m pytest fixes/tests --junitxml="%ARTIFACTS_DIR%\pytest.xml" --log-cli-level=INFO
