# Export Model to ONNX

Export trained PyTorch model to ONNX format for CPU/edge deployment.

## Usage
```
/export-onnx [model_path] [opset] [simplify]
```

## Examples
```
/export-onnx runs/train/yolov8n-traffic-v1/weights/best.pt
/export-onnx models/yolov8n-traffic/v1.0.0/best.pt 12 true
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

MODEL_PATH=${1:-"runs/train/yolov8n-traffic-v1/weights/best.pt"}
OPSET=${2:-12}
SIMPLIFY=${3:-true}

cd /path/to/project
source .venv/bin/activate

python -c "
from ultralytics import YOLO
model = YOLO('$MODEL_PATH')
model.export(format='onnx', opset=$OPSET, simplify=$SIMPLIFY, dynamic=False)
print('Exported to:', model.ckpt_path.replace('.pt', '.onnx'))
"

echo "ONNX export complete."
```

## Output
- `{model_name}.onnx` - FP32 ONNX model
- Use `export-trt` for TensorRT conversion on Jetson.
