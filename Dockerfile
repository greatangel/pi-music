# Use Python 3.11 Alpine for lightweight, fast, and reliable builds on Raspberry Pi
FROM python:3.11-alpine

# Install system runtime dependencies for audio and Discord voice (FFmpeg, Opus, Sodium)
RUN apk add --no-cache \
    ffmpeg \
    opus \
    libsodium \
    ca-certificates

# Create non-root user for security
RUN adduser -D -s /bin/sh appuser

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies (PyNaCl has prebuilt musllinux wheels for ARM64)
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Start the bot
CMD ["python", "bot.py"]
