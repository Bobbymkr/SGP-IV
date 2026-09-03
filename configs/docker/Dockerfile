# Adaptive Traffic Signal Timer - Production Dockerfile
# ===================================================

# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libvpx-dev \
    pkg-config \
    wget \
    curl \
    git \
    supervisor \
    nginx \
    redis-tools \
    htop \
    iotop \
    net-tools \
    iproute2 \
    ufw \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install -e ".[prod]"

# Copy application code
COPY src/ ./src/
COPY configs/ ./configs/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models /app/uploads /app/static /app/cache

# Set permissions
RUN chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8501 9090

# Default command - run API server
CMD ["uvicorn", "adaptive_traffic.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
