# Run Simulation with Real Detection

Run the Pygame traffic simulation with live YOLOv8 detection.

## Usage
```
/run-simulation [config] [model]
```

## Examples
```
/run-simulation
/run-simulation config/simulation.yaml models/yolov8n-traffic/v1.0.0/best.onnx
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

CONFIG=${1:-"config/simulation.yaml"}
MODEL=${2:-"models/yolov8n-traffic/v1.0.0/best.onnx"}

cd /path/to/project/Code/YOLO/darkflow
source ../../.venv/bin/activate

python simulation_enhanced.py \
  --config $CONFIG \
  --model $MODEL \
  --headless false
```

## Headless Mode (CI/CD)
```bash
xvfb-run -a python simulation_enhanced.py --config config/simulation.yaml --model $MODEL --headless true
```
