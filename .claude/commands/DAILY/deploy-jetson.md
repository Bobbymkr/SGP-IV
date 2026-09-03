# Deploy to Jetson Edge Device

Deploy optimized model and inference code to Jetson Orin.

## Usage
```
/deploy-jetson [jetson_ip] [model_version]
```

## Examples
```
/deploy-jetson 192.168.1.100 v1.0.0
/deploy-jetson jetson-orin.local latest
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

JETSON_IP=${1:-"jetson-orin.local"}
VERSION=${2:-"latest"}

cd /path/to/project

# Build Docker image for Jetson (ARM64)
docker buildx build --platform linux/arm64 -t traffic-signal:$VERSION -f Dockerfile.jetson .

# Save and transfer
docker save traffic-signal:$VERSION | gzip | ssh ubuntu@$JETSON_IP "docker load"

# Deploy on Jetson
ssh ubuntu@$JETSON_IP << EOF
  cd /home/ubuntu/traffic-signal
  docker compose down
  docker compose up -d
  docker system prune -f
EOF

echo "Deployment to $JETSON_IP complete."
```

## Prerequisites
- SSH access to Jetson
- Docker + Docker Compose on Jetson
- JetPack 6.0+ with TensorRT
- Model files in `models/` directory

## Dockerfile.jetson
```dockerfile
FROM nvcr.io/nvidia/l4t-jetpack:r36.3.0
WORKDIR /app
COPY requirements-jetson.txt .
RUN pip install -r requirements-jetson.txt
COPY src/ ./src/
COPY models/ ./models/
CMD ["python", "src/edge/main_loop.py"]
```
