#!/bin/bash
# Run test suite

set -e

# Activate venv if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Running tests..."
python -m pytest test_user_module.py -v --tb=short --color=yes -ra

echo ""
echo "Test execution complete!"
exit 0
