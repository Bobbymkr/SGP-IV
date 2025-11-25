
# Adaptive Traffic Signal System - Deployment Guide

## Overview
This document provides comprehensive deployment instructions for the Adaptive Traffic Signal System.

## System Components

### Core Services
- **traffic-controller**: Main traffic management service (Port 8000)
- **vehicle-detection**: YOLO-based vehicle detection (Port 8001)
- **streaming-service**: Real-time data streaming (Port 8002)
- **analytics-service**: Predictive analytics (Port 8003)
- **environmental-service**: Environmental integration (Port 8004)
- **dashboard**: Analytics dashboard (Port 8501)

### Infrastructure Services
- **postgres**: PostgreSQL database (Port 5432)
- **redis**: Redis cache (Port 6379)
- **kafka**: Apache Kafka messaging (Port 9092)
- **prometheus**: Monitoring (Port 9090)
- **grafana**: Visualization (Port 3000)
- **nginx**: Load balancer (Ports 80, 443)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- NVIDIA Docker runtime (for GPU support)
- At least 16GB RAM
- At least 50GB storage

### Deployment Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd adaptive-traffic-signal-timer
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Deploy System**
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

4. **Verify Deployment**
   ```bash
   ./scripts/health_check.sh
   ```

## Configuration

### Environment Variables
- `ENVIRONMENT`: development, staging, or production
- `WEATHER_API_KEY`: API key for weather services
- `AIR_QUALITY_API_KEY`: API key for air quality data
- `DB_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `JWT_SECRET`: JWT secret key

### Model Configuration
- YOLO model path: `./models/yolov8n.pt`
- Confidence threshold: 0.7 (production)
- Device: CUDA (GPU) or CPU

## Monitoring

### Access Points
- Grafana Dashboard: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Traffic Dashboard: http://localhost:8501

### Metrics
- Vehicle detection rate
- System response time
- Active intersections
- Error rates
- Resource utilization

## Maintenance

### Backup
```bash
./scripts/backup.sh
```

### Health Checks
```bash
./scripts/health_check.sh
```

### Rollback
```bash
PREVIOUS_VERSION=<commit-hash> ./scripts/rollback.sh
```

## Scaling

### Horizontal Scaling
```bash
docker-compose up -d --scale vehicle-detection=3
```

### Resource Allocation
Modify resource limits in `docker-compose.yml` based on your infrastructure.

## Security

### Network Security
- All services run in isolated Docker network
- Only necessary ports exposed
- SSL/TLS termination at nginx

### Data Security
- Database connections encrypted
- API authentication required
- Rate limiting enabled

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   - Ensure NVIDIA Docker runtime is installed
   - Check GPU availability with `nvidia-smi`

2. **High Memory Usage**
   - Reduce batch size in YOLO configuration
   - Scale down number of services

3. **Database Connection Issues**
   - Verify database is running: `docker-compose ps postgres`
   - Check connection string in environment

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f traffic-controller
```

## Performance Tuning

### Optimization Tips
1. Enable GPU acceleration for YOLO
2. Optimize database query performance
3. Implement caching strategies
4. Monitor resource utilization

### Benchmarks
- Vehicle Detection: ~100ms per frame (GPU)
- System Response: <200ms average
- Throughput: 1000+ operations/second

Generated: 2025-11-25T16:35:15.397370
Version: 2.1.0
