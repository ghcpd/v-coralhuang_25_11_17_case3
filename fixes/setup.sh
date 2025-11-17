#!/bin/bash
# Setup script to create venv and install dependencies

set -e

echo "Creating Python virtual environment..."
python -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! Virtual environment created at ./venv"
echo "To activate: source venv/bin/activate"
