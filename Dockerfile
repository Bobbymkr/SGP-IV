# Production Deployment Configuration
# ======================================

# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
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
RUN useradd -m -u trafficuser trafficuser

# Copy requirements first
COPY requirements-production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models /app/config /app/uploads /app/static /app/cache

# Set permissions
RUN chown -R trafficuser:trafficuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Switch to non-root user
USER trafficuser

# Expose ports
EXPOSE 8000 8080 9090

# Default command
CMD ["python", "run_production.py"]