# ML Rules for Adaptive-Traffic-Signal-Timer

## Model Versioning
- All models tracked in `models/` directory with semantic versioning
- Format: `model_name-v{MAJOR}.{MINOR}.{PATCH}.{format}`
- Example: `yolov8n-traffic-v1.2.0.onnx`
- Git LFS for files > 100MB

## Experiment Tracking
- Every training run logged with:
  - Hyperparameters (lr, batch, epochs, augmentations)
  - Dataset version (hash of annotations)
  - Hardware (GPU type, VRAM)
  - Metrics (mAP@0.5, mAP@0.5:0.95, per-class AP)
  - Inference latency (CPU, GPU, TensorRT)

## Data Contracts
- Annotations: YOLO format (class_id x_center y_center width height) normalized
- Dataset splits: train/val/test = 70/20/10, stratified by class
- Class names fixed: `['car', 'bus', 'truck', 'bike', 'rickshaw']`
- Image size: 640x640 (training), 640x640 or 1280x1280 (inference)

## Training Standards
- Base model: `yolov8n.pt` (COCO pre-trained) for transfer learning
- Epochs: 100 with early stopping (patience=20)
- Batch size: 16 (adjust for VRAM)
- Optimizer: SGD with momentum=0.937, weight_decay=0.0005
- LR schedule: cosine annealing with warmup (3 epochs)
- Augmentations: mosaic, mixup, copy-paste, HSV, flip, perspective

## Export & Optimization
```python
# PyTorch → ONNX (CPU/ONNX Runtime)
model.export(format='onnx', opset=12, simplify=True, dynamic=False)

# ONNX → TensorRT (Jetson)
trtexec --onnx=model.onnx --fp16 --saveEngine=model.trt --workspace=4096

# INT8 calibration (100-500 representative images)
trtexec --onnx=model.onnx --int8 --calib=calib_cache --saveEngine=model_int8.trt
```

## Inference Standards
- Warmup: 10 dummy forward passes before timing
- Batch size 1 for real-time (latency critical)
- FP16 on GPU, FP32 on CPU
- NMS: conf_thres=0.25, iou_thres=0.45, max_det=300

## Model Registry
```
models/
├── yolov8n-traffic/
│   ├── v1.0.0/
│   │   ├── best.pt          # PyTorch checkpoint
│   │   ├── best.onnx        # ONNX FP32
│   │   ├── best_fp16.onnx   # ONNX FP16
│   │   ├── calib.cache      # INT8 calibration cache
│   │   ├── metrics.json     # mAP, latency, etc.
│   │   └── config.yaml      # Training config
│   └── latest -> v1.0.0/
└── dqn-signal-control/
    └── v1.0.0/
        ├── policy.onnx
        └── config.yaml
```

## CI/CD Gates
- PR must pass: mAP@0.5 >= 0.75 (or previous best - 0.02)
- Inference latency: CPU < 50ms, Jetson TensorRT < 15ms
- Model size: ONNX < 50MB for edge deployment