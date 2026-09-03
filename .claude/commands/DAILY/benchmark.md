# Benchmark Model Inference

Benchmark model latency and throughput on CPU and GPU.

## Usage
```
/benchmark [model] [device] [iterations]
```

## Examples
```
/benchmark models/yolov8n-traffic/v1.0.0/best.onnx cpu 100
/benchmark models/yolov8n-traffic/v1.0.0/best.pt cuda 500
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

MODEL=${1:-"models/yolov8n-traffic/v1.0.0/best.onnx"}
DEVICE=${2:-"cpu"}
ITERATIONS=${3:-100}

cd /path/to/project
source .venv/bin/activate

python -c "
import time
import numpy as np
import onnxruntime as ort

# Load model
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if '$DEVICE' == 'cuda' else ['CPUExecutionProvider']
session = ort.InferenceSession('$MODEL', providers=providers)

# Warmup
dummy = np.random.randn(1, 3, 640, 640).astype(np.float32)
for _ in range(10):
    session.run(None, {'images': dummy})

# Benchmark
times = []
for _ in range($ITERATIONS):
    start = time.perf_counter()
    session.run(None, {'images': dummy})
    times.append(time.perf_counter() - start)

times = np.array(times) * 1000  # ms
print(f'Iterations: $ITERATIONS')
print(f'Device: $DEVICE')
print(f'Mean: {times.mean():.2f} ms')
print(f'Median: {np.median(times):.2f} ms')
print(f'P95: {np.percentile(times, 95):.2f} ms')
print(f'P99: {np.percentile(times, 99):.2f} ms')
print(f'FPS: {1000/times.mean():.1f}')
"
```

## Output Metrics
- Mean/Median latency (ms)
- P95/P99 latency (ms)
- Throughput (FPS)
- Memory usage (if available)
