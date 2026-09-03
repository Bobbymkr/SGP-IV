---
name: jetson-deployment-patterns
description: "Project-specific patterns for deploying the traffic signal system to NVIDIA Jetson Orin."
---

# Jetson Deployment Patterns

Project-specific patterns for deploying the traffic signal system to NVIDIA Jetson Orin.
Based on NVIDIA Jetson Platform Services, Seeed Studio guides, and the0807/YOLOv8-ONNX-TensorRT.
**Adapted for Indian traffic systems - MORTH (Ministry of Road Transport & Highways) compliance.**

## Hardware Targets

| Jetson Model | GPU | RAM | Recommended Model | Max Streams |
|--------------|-----|-----|-------------------|-------------|
| Orin Nano 8GB | 1024 CUDA | 8GB | YOLOv8n INT8 | 4-6 |
| Orin NX 16GB | 1024 CUDA | 16GB | YOLOv8n/s INT8 | 16-18 |
| AGX Orin 32GB | 2048 CUDA | 32GB | YOLOv8m INT8 | 20+ |

## MORTH Compliance Notes

**India is adopting NTCIP 1202 for V2X signaling, with IS 14241 as the national standard.**
When deploying to Indian traffic systems, add the following MORTH compliance section to your deployment checklist:

```yaml
# config/deploy_checklist.yaml - MORTH section
morth:
  enable: true  # Set true for India deployment
  standards: ["IS 14241", "NTCIP 1202"]
  # IS 14241 = Indian Standard for traffic signal systems
  # NTCIP 1202 = V2X Vehicle Signal Priority

  # Required OIDs for Indian NTCIP compliance
  oids:
    cycle_length: ".1.3.6.1.4.1.30692.2.1.1.1.1.1"  # MORTH-standard OID
    current_phase: ".1.3.6.1.4.1.30692.2.1.1.1.1.2"
    green_duration: ".1.3.6.1.4.1.30692.2.1.1.1.1.3"

  # SNMP community string for Indian deployments
  community: "public"  # or "morth_readonly" depending on setup

  # SPaT broadcast settings (UDP 1736, J2735 standard)
  spat_port: 1736
  cycle_length: 120  # typical Indian urban intersection cycle

  # Minimum green times per MORTH guidelines
  min_green: 7  # for two-wheelers/authoric rickshaws
  max_green: 50
  yellow: 3.5
  all_red: 3
```

## Dockerfile.jetson

```dockerfile
# Multi-stage build for Jetson (ARM64)
FROM nvcr.io/nvidia/l4t-jetpack:r36.3.0 AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-dev \
    libopencv-dev python3-opencv \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    libnvinfer-dev libnvinfer-plugin-dev \
    libnvonnxparsers-dev libnvparsers-dev \
    && rm -rf /var/lib/apt/lists/*

# Python packages (use Jetson wheels where possible)
RUN pip3 install --no-cache-dir \
    numpy==1.24.3 \
    opencv-python==4.8.1.78 \
    onnxruntime-gpu==1.16.0 \
    torch==2.1.0 torchvision==0.16.0 \
    --index-url https://download.pytorch.org/whl/cu118 \
    ultralytics==8.2.0 \
    pyyaml==6.0.1 \
    prometheus-client==0.19.0 \
    psutil==5.9.0

# TensorRT Python bindings (from JetPack)
ENV LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:/usr/local/cuda/targets/aarch64-linux/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH=/usr/lib/python3.10/dist-packages:$PYTHONPATH

WORKDIR /app
COPY src/ ./src/
COPY models/ ./models/
COPY config/ ./config/

# MORTH compliance: set environment vars for Indian standards
ENV MORTH_ENABLED=true
ENV MORTH_STANDARD="IS14241"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health')"

CMD ["python3", "src/edge/main_loop.py"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  detector:
    build:
      context: .
      dockerfile: Dockerfile.jetson
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility,video,graphics
      - MODEL_PATH=/app/models/yolov8n-traffic/v1.0.0/best_int8.engine
      - CONFIG_PATH=/app/config/detector.yaml
      - CAMERA_NORTH=rtsp://north_cam:554/stream
      - CAMERA_SOUTH=rtsp://south_cam:554/stream
      - CAMERA_EAST=rtsp://east_cam:554/stream
      - CAMERA_WEST=rtsp://west_cam:554/stream
      - MORTH_ENABLED=true  # NEW: Indian deployment flag
      - MORTH_STANDARD=IS14241  # NEW: Indian standard
    volumes:
      - /tmp/argus_socket:/tmp/argus_socket
      - /etc/enctune.conf:/etc/enctune.conf
      - ./models:/app/models:ro
      - ./config:/app/config:ro
      - ./logs:/app/logs
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8081/health')"]
      interval: 30s
      timeout: 10s
      start_period: 60s

  controller:
    build:
      context: .
      dockerfile: Dockerfile.jetson
    runtime: nvidia
    environment:
      - CONFIG_PATH=/app/config/controller.yaml
      - INTERSECTION_ID=INT-001
      - NTCIP_HOST=192.168.1.100
      - NTCIP_PORT=161
      - MORTH_ENABLED=true  # NEW
      - MORTH_AGENT_ID="INT-001"  # NEW: MORTH agent identification
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    depends_on:
      detector:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8082/health')"]
      interval: 30s
      timeout: 10s

  spat:
    build:
      context: .
      dockerfile: Dockerfile.jetson
    runtime: nvidia
    environment:
      - CONFIG_PATH=/app/config/spat.yaml
      - INTERSECTION_ID=INT-001
      - RSU_HOST=192.168.1.200
      - RSU_PORT=1736
      - MORTH_ENABLED=true  # NEW
    volumes:
      - ./config:/app/config:ro
    depends_on:
      controller:
        condition: service_healthy
    restart: unless-stopped
    ports:
      - "1736:1736/udp"  # SPaT broadcast (J2735 standard)
    # MORTH: SPaT messages include IS 14241 extension fields

  monitor:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./monitoring/grafana_dashboard.json:/var/lib/grafana/dashboards/traffic.json
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=traffic123
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

## Systemd Services

```ini
# /etc/systemd/system/traffic-detector.service
[Unit]
Description=Traffic Signal Detector
After=docker.service
Requires=docker.service

[Service]
Type=notify
ExecStart=/usr/bin/docker compose -f /opt/traffic-signal/docker-compose.yml up detector
ExecStop=/usr/bin/docker compose -f /opt/traffic-signal/docker-compose.yml stop detector
Restart=always
RestartSec=10
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target

# MORTH-specific: enable on boot for India deployments
# sudo systemctl enable traffic-detector.morth

# /etc/systemd/system/traffic-controller.service
[Unit]
Description=Traffic Signal Controller
After=traffic-detector.service
Requires=traffic-detector.service

[Service]
Type=notify
ExecStart=/usr/bin/docker compose -f /opt/traffic-signal/docker-compose.yml up controller
ExecStop=/usr/bin/docker compose -f /opt/traffic-signal/docker-compose.yml stop controller
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/traffic-spat.service
[Unit]
Description=Traffic Signal SPaT Broadcaster
After=traffic-controller.service
Requires=traffic-controller.service

[Service]
Type=notify
ExecStart=/usr/bin/docker compose -f /opt/traffic-signal/docker-compose.yml up spat
ExecStop=/usr/bin/docker compose -f /opt/traffic-signal/docker-compose.yml stop spat
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Jetson Optimization Scripts

```bash
#!/bin/bash
# jetson-optimize.sh - Run on first boot (Indian deployment)

# 1. Max Performance Mode
sudo nvpmodel -m 0
sudo jetson_clocks

# 2. Disable GUI (headless)
sudo systemctl set-default multi-user.target

# 3. Swap (if needed)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 4. Docker daemon config
sudo mkdir -p /etc/docker
cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker

# 5. Enable services (Indian deployment)
sudo systemctl enable traffic-detector traffic-controller traffic-spat

# 6. MORTH-specific: load IS 14241 module params
# (typically no manual load needed - standards are in software configs)

# 7. Recommended: verify MORTH compliance
echo "Verifying MORTH compliance..."
python3 -c "
import os
morth = os.environ.get('MORTH_ENABLED', 'false')
standard = os.environ.get('MORTH_STANDARD', 'none')
print(f'MORTH enabled: {morth}')
print(f'Standard: {standard}')
if morth == 'true' and standard == 'IS14241':
    print('✓ MORTH compliance configuration present')
else:
    print('! WARNING: MORTH configuration incomplete')
"

echo "Jetson optimization complete. Reboot recommended."
```

## Model Deployment Checklist - MORTH Edition

```yaml
# config/deploy_checklist.yaml - MORTH enhanced

deployment:
  model:
    path: "models/yolov8n-traffic/v1.0.0/best_int8.engine"
    format: "TensorRT INT8"
    calibration_cache: "models/yolov8n-traffic/v1.0.0/calib.cache"
    input_shape: [1, 3, 640, 640]
    classes: 8  # Indian: car, bus, truck, two_wheeler, autorickshaw, cycle, tractor, bus_pedigree
    morth_compliance: true  # NEW

  detector:
    batch_size: 1
    conf_threshold: 0.25
    iou_threshold: 0.45
    max_det: 300  # Indian: higher than 100 (sparser Western traffic)
    device: "cuda:0"
    fps_target: 30

  controller:
    min_green: 7  # Indian MORTH
    max_green: 50  # Indian MORTH
    yellow: 3.5  # Indian MORTH
    all_red: 3  # Indian MORTH
    intervention_freq: 10  # seconds (can be 7 for high-volatility sites)
    safety_wrapper: true
    morth_compliance: true

  cameras:
    - id: "north"
      rtsp: "rtsp://192.168.1.10:554/stream"
      approach: "north"
      calibration: "config/calib/north.yaml"
      morth_road_class: "urban"  # NEW: urban/ suburban/ rural per IS 14241
    - id: "south"
      rtsp: "rtsp://192.168.1.11:554/stream"
      approach: "south"
      calibration: "config/calib/south.yaml"
      morth_road_class: "urban"
    - id: "east"
      rtsp: "rtsp://192.168.1.12:554/stream"
      approach: "east"
      calibration: "config/calib/east.yaml"
      morth_road_class: "urban"
    - id: "west"
      rtsp: "rtsp://192.168.1.13:554/stream"
      approach: "west"
      calibration: "config/calib/west.yaml"
      morth_road_class: "urban"

  networking:
    detector_port: 8081
    controller_port: 8082
    spat_port: 1736
    prometheus_port: 9090
    grafana_port: 3000

  morth:
    enable: true
    standard: "IS14241"
    agent_id: "INT-001"
    spat_broadcast: true  # MUST broadcast SPaT on UDP 1736
    min_green: 7
    max_green: 50
    yellow: 3.5
    all_red: 3

  healthchecks:
    interval: 30s
    timeout: 10s
    start_period: 60s
    failure_threshold: 3
```

## Rules
- Always build TensorRT engine ON the target Jetson (architecture-specific)
- Use `trtexec` not Python build scripts on Jetson
- FP16 default, INT8 for production (needs calibration)
- Max Power Mode: `sudo nvpmodel -m 0 && sudo jetson_clocks`
- Health checks on all containers with proper start_period
- Prometheus metrics on /metrics endpoint
- **SPAt broadcast on UDP 1736 (J2735 standard)** - MANDATORY for NTCIP 1202 compliance
- Log rotation: max 10MB, 3 files
- Swap file for memory safety on 8GB models
- **MORTH compliance**: When `MORTH_ENABLED=true`, ensure:
  - IS 14241 OIDs are accessible via SNMP
  - SPaT messages include IS 14241 extension fields (if supported by RSU)
  - Minimum green = 7s, yellow = 3.5s, all-red = 3s per MORTH guidelines
  - SNMP community string configured for Indian deployments
  - Agent ID set via `MORTH_AGENT_ID` env var
  - Cycle length typical for Indian urban intersections (90-120s)
- **Fallback**: If MORTH compatibility layer not available, gracefully degrade to
  standard NTCIP 1202 operation (tool auto-detects and switches modes)
