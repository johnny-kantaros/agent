# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install pip build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies (using pip)
RUN pip install --no-cache-dir "uvicorn[standard]" && \
    pip install --no-cache-dir .

# Copy source code
COPY ./src ./src

# Ensure stdout/stderr is unbuffered (logs show up in Fly)
ENV PYTHONUNBUFFERED=1

# Use $PORT provided by Fly
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]