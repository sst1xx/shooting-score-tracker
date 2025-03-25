# Lightweight Python base image
FROM python:3.11-slim AS build

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Copy only requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create final image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/app/data

# Set working directory
WORKDIR /app

# Create the data directory with proper permissions
RUN mkdir -p /app/data && \
    addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app/data

# Copy installed dependencies from build stage
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code directly to /app
COPY src/. /app/
COPY README.md /app/
COPY policy.pdf /app/

# Set correct ownership after all files are copied
RUN chown -R appuser:appgroup /app

# Create the data volume with the correct path
VOLUME ["/app/data"]

# Change to non-root user
USER appuser

# Add metadata
LABEL maintainer="Telegram Shooting Bot Maintainer" \
      description="Telegram bot for shooting results tracking" \
      version="1.0.0"

# Set the default command to run main.py directly
CMD ["python", "main.py"]