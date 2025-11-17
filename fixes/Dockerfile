FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports if needed
EXPOSE 5000

# Default command: run tests
CMD ["python", "-m", "pytest", "test_user_module.py", "-v", "--tb=short", "--color=yes"]
