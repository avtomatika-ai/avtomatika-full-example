# Standalone Dockerfile for the example repository
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (graphviz for blueprint rendering)
RUN apt-get update && apt-get install -y \
    graphviz \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and metadata first
COPY pyproject.toml .
COPY README.md .

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install python dependencies
RUN pip install --no-cache-dir .[test]

# Copy the rest of the application code
COPY . .

# Default command to run the orchestrator
CMD ["python", "full_example.py"]
