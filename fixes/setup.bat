@echo off
REM Setup script to create venv and install dependencies

setlocal enabledelayedexpansion

echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete! Virtual environment created at .\venv
echo To activate: .\venv\Scripts\activate.bat
exit /b 0
