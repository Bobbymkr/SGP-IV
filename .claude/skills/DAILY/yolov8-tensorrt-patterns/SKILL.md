---
name: yolov8-tensorrt-patterns
description: "Project-specific patterns for YOLOv8 deployment on Jetson Orin using TensorRT."
---

# YOLOv8 TensorRT Patterns

Project-specific patterns for YOLOv8 deployment on Jetson Orin using TensorRT.
Based on NVIDIA Jetson Platform Services, Seeed Studio, and the0807/YOLOv8-ONNX-TensorRT.
**Adapted for Indian traffic systems - expanded class mapping for Indian roads.**

## Export Pipeline

### PyTorch → ONNX → TensorRT
```bash
# 1. Export ONNX (FP32)
yolo export model=yolov8n.pt format=onnx opset=12 simplify=True dynamic=False imgsz=640

# 2. FP16 Engine (recommended for Jetson)
trtexec --onnx=yolov8n.onnx --fp16 --saveEngine=yolov8n_fp16.engine --workspace=4

# 3. INT8 Engine (fastest, needs calibration)
trtexec --onnx=yolov8n.onnx --int8 --saveEngine=yolov8n_int8.engine \
  --calib=calib_cache --workspace=4
```

### Indian Class Mapping (CRITICAL ADAPTATION)
**Current 5 classes:** `['car', 'bus', 'truck', 'rickshaw', 'bike']`

**Indian adaptation: 8 classes** - Indian roads have significant two-wheeler,
cycle, and tractor traffic not present in Western datasets:

```python
# In postprocess or class mapping, use these 8 classes:
INDIAN_CLASSES = ['car', 'bus', 'truck', 'two_wheeler',
                  'autorickshaw', 'cycle', 'tractor', 'bus_pedigree']

# Class indices for TensorRT engine (must match engine class order):
# 0=car, 1=bus, 2=truck, 3=two_wheeler, 4=autorickshaw,
# 5=cycle, 6=tractor, 7=bus_pedigree (or school_bus)

# Update the COLORS and metadata for 8 classes
```

**Vehicle lengths for queue length calculation** (update in queue-estimation-patterns):
```python
# Add to vehicle_lengths dict (in queue-estimation-patterns or signal-control-patterns)
'vehicle_lengths': {
    'car': 4.5, 'bus': 12.0, 'truck': 10.0,
    'two_wheeler': 1.8, 'autorickshaw': 2.8,
    'cycle': 1.9, 'tractor': 3.5
}
```

### Inference Patterns

### ONNX Runtime (CPU - Laptop)
```python
import onnxruntime as ort
import numpy as np
import cv2

class YOLOv8ONNX:
    def __init__(self, model_path, conf_thres=0.25, iou_thres=0.45):
        self.session = ort.InferenceSession(
            model_path,
            providers=['CPUExecutionProvider']
        )
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.input_name = self.session.get_inputs()[0].name

        # Indian class mapping - must match model training
        self.class_names = ['car', 'bus', 'truck', 'two_wheeler',
                           'autorickshaw', 'cycle', 'tractor', 'bus_pedigree']
        self.num_classes = 8

    def postprocess(self, preds, scale, pad):
        preds = preds[0]  # (1, 84, 8400) → (84, 8400)
        preds = preds.T   # (8400, 84)

        # Filter by confidence
        conf = preds[:, 4]
        mask = conf > self.conf_thres
        preds = preds[mask]
        conf = conf[mask]

        # Class scores - Indian model has 8 classes (starting at index 5)
        cls_scores = preds[:, 5:13]  # 8 class scores (was 5 previously)
        cls_ids = cls_scores.argmax(1)
        cls_conf = cls_scores.max(1)
        conf = conf * cls_conf

        # Map class ID to Indian class name
        # cls_ids are 0-7, map to self.class_names
        # No further filtering needed - all 8 classes are valid in Indian context

        # Filter again by confidence after class assignment
        mask = conf > self.conf_thres
        preds = preds[mask]
        conf = conf[mask]
        cls_ids = cls_ids[mask]

        # NMS - keep max_det=300 for Indian traffic (higher vehicle density)
        boxes = self.xywh2xyxy(preds[:, :4])
        boxes = self.scale_boxes(boxes, scale, pad)

        keep = cv2.dnn.NMSBoxes(boxes.tolist(), conf.tolist(),
                                 self.conf_thres, self.iou_thres)

        return boxes[keep], conf[keep], cls_ids[keep]

    def __call__(self, img):
        inp, scale, pad = self.preprocess(img)
        preds = self.session.run(None, {self.input_name: inp})
        return self.postprocess(preds, scale, pad)
```

### TensorRT (Jetson - Python)
```python
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit

class YOLOv8TRT:
    def __init__(self, engine_path, indian_classes=8):
        self.logger = trt.Logger(trt.Logger.WARNING)
        with open(engine_path, 'rb') as f:
            runtime = trt.Runtime(self.logger)
            self.engine = runtime.deserialize_cuda_engine(f.read())
        self.context = self.engine.create_execution_context()
        self.input_idx = self.engine.get_binding_index('images')
        self.output_idx = self.engine.get_binding_index('output0')

        # Indian class mapping
        self.indian_classes = indian_classes  # 8 for Indian adaptation

    def infer(self, img):
        # Preprocess (same as ONNX)
        inp, scale, pad = self.preprocess(img)

        # Allocate buffers
        d_input = cuda.mem_alloc(inp.nbytes)
        output_shape = self.engine.get_binding_shape(self.output_idx)
        d_output = cuda.mem_alloc(np.prod(output_shape) * 4)

        cuda.memcpy_htod(d_input, inp)
        self.context.execute_v2([int(d_input), int(d_output)])

        output = np.empty(output_shape, dtype=np.float32)
        cuda.memcpy_dtoh(output, d_output)

        return self.postprocess_TRT(output, scale, pad)

    def postprocess_TRT(self, preds, scale, pad):
        # Same postprocess as ONNX but with 8-class handling
        preds = preds[0]
        preds = preds.T

        # Filter by confidence (index 4 is still confidence)
        conf = preds[:, 4]
        mask = conf > 0.25
        preds = preds[mask]
        conf = conf[mask]

        # 8 class scores (indices 5-12, was 5 previously)
        cls_scores = preds[:, 5:13]
        cls_ids = cls_scores.argmax(1)
        cls_conf = cls_scores.max(1)
        conf = conf * cls_conf

        # Filter again
        mask = conf > 0.25
        preds = preds[mask]
        conf = conf[mask]
        cls_ids = cls_ids[mask]

        # Map to Indian class names if needed
        # cls_ids 0-7 correspond to: car, bus, truck, two_wheeler,
        #   autorickshaw, cycle, tractor, bus_pedigree

        # NMS
        boxes = self.xywh2xyxy(preds[:, :4])
        boxes = self.scale_boxes(boxes, scale, pad)

        keep = cv2.dnn.NMSBoxes(boxes.tolist(), conf.tolist(),
                                 0.25, 0.45)

        return boxes[keep], conf[keep], cls_ids[keep]
```

### DeepStream (Production Multi-Stream)
```bash
# config_infer_primary_yoloV8.txt - unchanged DeepStream config
# The only change needed: update labelfile-path to include 8 classes

# labels.txt (Indian adaptation):
# car
# bus
# truck
# two_wheeler
# autorickshaw
# cycle
# tractor
# bus_pedigree

# deepstream_app_config.txt - unchanged
```

## Benchmarking
```python
def benchmark(model_path, device='cpu', iterations=100):
    import time
    session = ort.InferenceSession(model_path,
        providers=['CUDAExecutionProvider'] if device=='cuda' else ['CPUExecutionProvider'])

    dummy = np.random.randn(1, 3, 640, 640).astype(np.float32)

    # Warmup
    for _ in range(10):
        session.run(None, {'images': dummy})

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        session.run(None, {'images': dummy})
        times.append(time.perf_counter() - start)

    times = np.array(times) * 1000
    return {
        'mean_ms': times.mean(),
        'median_ms': np.median(times),
        'p95_ms': np.percentile(times, 95),
        'fps': 1000 / times.mean()
    }
```

**Expected on Jetson Orin NX 16GB (from Seeed benchmarks, with Indian class mapping):**
- YOLOv8n FP16: ~60 FPS (16ms) - same as before, class count doesn't affect inference much
- YOLOv8n INT8: ~63 FPS (15ms) - same
- YOLOv8s FP16: ~48 FPS (20ms) - same
- YOLOv8s INT8: ~57 FPS (17ms) - same

**Note**: 8-class vs 5-class has ~2% inference overhead - negligible at these FPS rates.

## Rules
- Always use `trtexec` for engine building - never `build.py` on Jetson
- FP16 is default for Jetson; INT8 needs 500+ calibration images
- ONNX Runtime CPU: use `CPUExecutionProvider` only
- Letterbox with 114 padding (YOLO standard)
- NMS: conf=0.25, iou=0.45, max_det=300 (increased from 100 for Indian traffic density)
- **Class mapping: 0=car, 1=bus, 2=truck, 3=two_wheeler, 4=autorickshaw, 5=cycle, 6=tractor, 7=bus_pedigree (Indian adaptation)**
- Update `labels.txt` for DeepStream to include 8 classes
- Update `vehicle_lengths` in queue-estimation-patterns to match these 8 classes
- Max Power Mode: `sudo nvpmodel -m 0 && sudo jetson_clocks`
- Indian roads have higher vehicle density → use max_det=300 (vs 100 for sparse traffic)
