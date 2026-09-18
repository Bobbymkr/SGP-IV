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
    p.add_argument("--registry", default="models/registry/india-yolov8n-final",
                   help="onnx registry dir")
    p.add_argument("--frames", type=int, default=20)
    p.add_argument("--stages", action="store_true",
                   help="route detect+estimate through StagedPipeline")
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
    if args.stages:
        from adaptive_traffic.config.city_profile import get_city_profile  # noqa: E402
        from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator  # noqa: E402
        from adaptive_traffic.core.pipeline import StagedPipeline  # noqa: E402

        pipe = StagedPipeline(detector, QueueEstimator(get_city_profile("bangalore")))
        # Inline path: same stages the edge worker drains. The drop-oldest
        # buffer is bypassed by design — submit-all-then-drain would silently
        # drop frames (buffer < n) and skew the mean; buffer semantics are
        # covered by unit tests instead.
        results = [pipe.process(f) for f in frames]
        det_ms = est_ms = 0.0
        total = 0
        for res in results:
            det_ms += res.stage_ms["detect"]
            est_ms += res.stage_ms["estimate"]
            raw = res.detections
            total += len(raw.detections if hasattr(raw, "detections") else raw)
        n = len(results)
        print(f"backend={args.backend} stages=detect+estimate frames={n} "
              f"detect_ms={det_ms / n:.3f} estimate_ms={est_ms / n:.3f} det_total={total}")
        return 0
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
