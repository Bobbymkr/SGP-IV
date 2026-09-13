"""Detection latency benchmark — CPU baseline via the configured DetectorPort backend.
Record results in docs/BENCHMARKS.md (make bench-detect).

Uses synthetic frames: real traffic footage arrives with Phase T, at which point
swap --frames-dir to a captured set for realistic numbers.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_traffic.core.detection.base import DetectorPort  # noqa: E402


def synth_frames(n: int = 20, size: int = 640, seed: int = 42) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.integers(0, 255, (size, size, 3), dtype=np.uint8) for _ in range(n)]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backend", default="ultralytics", choices=["ultralytics", "onnx", "tensorrt"])
    p.add_argument("--model", default="yolov8n.pt", help="ultralytics model path")
    p.add_argument("--registry", default="models/registry/india-yolov8n", help="onnx registry dir")
    p.add_argument("--frames", type=int, default=20)
    args = p.parse_args()

    cfg = {"backend": args.backend}
    if args.backend == "ultralytics":
        cfg["model_path"] = args.model
    else:
        cfg["registry_dir"] = args.registry

    try:
        detector = DetectorPort.create(cfg)
    except (ImportError, ValueError, FileNotFoundError) as e:
        print(f"backend '{args.backend}' unavailable: {e}")
        return 1

    frames = synth_frames(args.frames)
    det = detector.detect(frames[0])  # warmup
    print(f"warmup detections: {len(det.detections)}")

    t0 = time.perf_counter()
    total = 0
    for f in frames:
        total += len(detector.detect(f).detections)
    elapsed = time.perf_counter() - t0

    fps = args.frames / elapsed
    lat_ms = elapsed / args.frames * 1000
    print(f"backend={args.backend} frames={args.frames} fps={fps:.2f} latency={lat_ms:.1f}ms/frame det_total={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())