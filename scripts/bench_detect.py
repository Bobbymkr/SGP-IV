"""Detection latency benchmark — CPU baseline via the configured DetectorPort backend.
Record results in docs/BENCHMARKS.md (make bench-detect).

Two frame sources:
- default: synthetic noise (latency-only; 0 detections expected)
- --frames-dir: real files from disk (recorded footage or rendered sets).
  Prints a per-frame detection histogram + per-class counts alongside fps,
  so a `det_total=0` row can no longer pass silently as a quality signal.
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from footage import det_hist, load_frames  # noqa: E402

from adaptive_traffic.core.detection.base import DetectorPort  # noqa: E402


def synth_frames(n: int = 20, size: int = 640, seed: int = 42) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.integers(0, 255, (size, size, 3), dtype=np.uint8) for _ in range(n)]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backend", default="ultralytics", choices=["ultralytics", "onnx", "tensorrt"])
    p.add_argument("--model", default="yolov8n.pt", help="ultralytics model path")
    p.add_argument(
        "--registry", default="models/registry/india-yolov8n-final", help="onnx registry dir"
    )
    p.add_argument("--frames", type=int, default=20)
    p.add_argument(
        "--frames-dir",
        default=None,
        help="directory of jpg/png frames (recorded footage or rendered set)",
    )
    p.add_argument(
        "--max-frames", type=int, default=0, help="cap frames from --frames-dir (0 = all)"
    )
    p.add_argument(
        "--stages", action="store_true", help="route detect+estimate through StagedPipeline"
    )
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

    source = "synth-noise"
    if args.frames_dir:
        frames, names, skipped = load_frames(args.frames_dir, args.max_frames)
        if not frames:
            print(f"no readable frames in {args.frames_dir} (skipped={skipped})")
            return 1
        source = f"frames-dir:{args.frames_dir}"
        if skipped:
            print(f"warning: skipped {skipped} unreadable files in {args.frames_dir}")
    else:
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
        counts, classes = [], Counter()
        for res in results:
            det_ms += res.stage_ms["detect"]
            est_ms += res.stage_ms["estimate"]
            raw = res.detections
            dets = raw.detections if hasattr(raw, "detections") else raw
            counts.append(len(dets))
            classes.update(d.class_name for d in dets)
        n = len(results)
        print(
            f"backend={args.backend} source={source} stages=detect+estimate frames={n} "
            f"detect_ms={det_ms / n:.3f} estimate_ms={est_ms / n:.3f} det_total={sum(counts)}"
        )
        print(f"det_hist={det_hist(counts)} class_counts={dict(classes)}")
        return 0
    det = detector.detect(frames[0])  # warmup
    print(f"warmup detections: {len(det.detections)}")

    t0 = time.perf_counter()
    counts, classes = [], Counter()
    for f in frames:
        dets = detector.detect(f).detections
        counts.append(len(dets))
        classes.update(d.class_name for d in dets)
    elapsed = time.perf_counter() - t0

    fps = len(frames) / elapsed
    lat_ms = elapsed / len(frames) * 1000
    print(
        f"backend={args.backend} source={source} frames={len(frames)} fps={fps:.2f} "
        f"latency={lat_ms:.1f}ms/frame det_total={sum(counts)}"
    )
    print(f"det_hist={det_hist(counts)} class_counts={dict(classes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
