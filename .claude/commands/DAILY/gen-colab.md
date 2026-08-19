# Generate Colab Notebooks

Create Colab notebooks for YOLO training, ONNX export, DQN training.

## Usage
```
/gen-colab [output_dir]
```

## Examples
```
/gen-colab colab/
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

OUTPUT_DIR=${1:-"colab"}

cd /path/to/project
mkdir -p $OUTPUT_DIR

# 01_yolo_finetune.ipynb
cat > $OUTPUT_DIR/01_yolo_finetune.ipynb << 'EOF'
{
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": ["# YOLOv8 Fine-tuning for Traffic Detection", "Train YOLOv8n on custom intersection footage."]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["!pip install ultralytics opencv-python pycocotools -q"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["from google.colab import drive", "drive.mount('/content/drive')"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["import os", "DATA_ROOT = '/content/drive/MyDrive/traffic_dataset'", "os.listdir(DATA_ROOT)"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["from ultralytics import YOLO", "model = YOLO('yolov8n.pt')"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["results = model.train(", "    data=f'{DATA_ROOT}/data.yaml',", "    epochs=100,", "    imgsz=640,", "    batch=16,", "    device=0,", "    patience=20,", "    augment=True,", "    mosaic=1.0,", "    mixup=0.1,", "    copy_paste=0.3,", "    project='runs/train',", "    name='yolov8n-traffic-v1',", "    exist_ok=True", ")"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["model.val()"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["model.export(format='onnx', opset=12, simplify=True, dynamic=False)"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["import shutil", "shutil.copytree('runs/train/yolov8n-traffic-v1', f'{DATA_ROOT}/models/yolov8n-traffic/v1.0.0', dirs_exist_ok=True)"]}
 ],
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.10"}},
 "nbformat": 4, "nbformat_minor": 4
}
EOF

# 02_export_onnx.ipynb
cat > $OUTPUT_DIR/02_export_onnx.ipynb << 'EOF'
{
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": ["# ONNX Export & Optimization"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["from ultralytics import YOLO", "model = YOLO('/content/drive/MyDrive/traffic_dataset/models/yolov8n-traffic/v1.0.0/best.pt')"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["model.export(format='onnx', opset=12, simplify=True)  # FP32", "model.export(format='onnx', opset=12, simplify=True, half=True)  # FP16"]},
  {"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["import onnx", "import onnxruntime as ort", "session = ort.InferenceSession('best.onnx', providers=['CPUExecutionProvider'])", "import numpy as np", "dummy = np.random.randn(1, 3, 640, 640).astype(np.float32)", "import time", "for _ in range(10): session.run(None, {'images': dummy})", "times = []", "for _ in range(100):", "    start = time.perf_counter()", "    session.run(None, {'images': dummy})", "    times.append(time.perf_counter() - start)", "print(f'CPU ONNX: {np.mean(times)*1000:.1f}ms avg, {1000/np.mean(times):.1f} FPS')"]}
 ],
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
 "nbformat": 4, "nbformat_minor": 4
}
EOF

echo "Colab notebooks generated in $OUTPUT_DIR/"
echo "Upload to Google Colab and run."
```

## Generated Notebooks
- `01_yolo_finetune.ipynb` - Full training pipeline
- `02_export_onnx.ipynb` - ONNX export + benchmark
- Add more as needed