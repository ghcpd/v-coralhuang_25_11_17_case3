@echo off
REM Windows batch script to run tests

setlocal enabledelayedexpansion

echo Checking for virtual environment...
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo Running tests...
python -m pytest test_user_module.py -v --tb=short --color=yes -ra
if errorlevel 1 (
    echo Test execution failed with error code %errorlevel%
    exit /b %errorlevel%
)

echo.
echo Test execution complete!
exit /b 0
