"""Queue-estimation error vs ground-truth counts (Phase B).

Two ground-truth sources (exactly one required):
- --labels-dir: YOLO label files for rendered sets (`<stem>.txt`, missing == 0).
  PROXY ONLY: labels count every visible vehicle while the estimator counts
  queue-zone vehicles, so expect systematic undercount — the value is the
  per-weather degradation gradient, not an absolute qerr claim.
- --gt-csv: hand-count CSV (`frame,count` header) for phone footage with no
  labels. THIS is the honest qerr path: capture 10 min fixed-mount 720p,
  hand-count 50 frames, run this script.

Prints RMSE/MAE/bias for detector counts AND estimator queue totals vs GT,
per-weather splits, and the tier-low hybrid trigger verdict (RMSE > 0.5).
"""

import argparse
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from footage import det_hist, err_stats, load_frames, parse_weather, read_gt_csv, yolo_gt_counts  # noqa: E402

from adaptive_traffic.config.city_profile import get_city_profile  # noqa: E402
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator  # noqa: E402
from adaptive_traffic.core.detection.base import DetectorPort  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames-dir", required=True)
    p.add_argument("--labels-dir", default=None)
    p.add_argument("--gt-csv", default=None, help="hand-count CSV (frame,count header)")
    p.add_argument("--backend", default="onnx", choices=["ultralytics", "onnx", "tensorrt"])
    p.add_argument("--model", default="yolov8n.pt")
    p.add_argument("--registry", default="models/registry/india-yolov8n-final")
    p.add_argument("--city", default="bangalore")
    p.add_argument("--conf", type=float, default=0.45, help="low-tier default")
    p.add_argument("--max-frames", type=int, default=0)
    p.add_argument("--out-csv", default=None)
    args = p.parse_args()

    if bool(args.labels_dir) == bool(args.gt_csv):
        print("pass exactly one of --labels-dir / --gt-csv")
        return 2

    frames, names, skipped = load_frames(args.frames_dir, args.max_frames)
    if not frames:
        print(f"no readable frames in {args.frames_dir}")
        return 1
    if skipped:
        print(f"warning: skipped {skipped} unreadable files")

    if args.gt_csv:
        gt_map = read_gt_csv(args.gt_csv)
        gt = [gt_map.get(Path(n).stem, 0) for n in names]
        gt_source = f"gt-csv:{args.gt_csv}"
    else:
        gt = yolo_gt_counts(args.labels_dir, [Path(n).stem for n in names])
        gt_source = f"labels:{args.labels_dir} (proxy — all visible vs queue-zone)"

    cfg = {"backend": args.backend, "confidence_threshold": args.conf}
    if args.backend == "ultralytics":
        cfg["model_path"] = args.model
    else:
        cfg["registry_dir"] = args.registry
    try:
        detector = DetectorPort.create(cfg)
    except (ImportError, ValueError, FileNotFoundError) as e:
        print(f"backend '{args.backend}' unavailable: {e}")
        return 1
    estimator = QueueEstimator(get_city_profile(args.city))

    pred_det, pred_queue, weathers = [], [], []
    t0 = time.perf_counter()
    for f, n in zip(frames, names):
        dets = detector.detect(f).detections
        pred_det.append(len(dets))
        pred_queue.append(estimator.estimate_from_detections(dets).total_vehicles)
        weathers.append(parse_weather(n))
    elapsed = time.perf_counter() - t0

    print(f"backend={args.backend} conf={args.conf} city={args.city} "
          f"frames={len(frames)} gt_source={gt_source} wall={elapsed:.1f}s")
    print(f"det_vs_gt   {err_stats(pred_det, gt)} hist={det_hist(pred_det)}")
    print(f"queue_vs_gt {err_stats(pred_queue, gt)} hist={det_hist(pred_queue)}")

    by_weather = defaultdict(lambda: ([], []))
    for w, pd, gt_ in zip(weathers, pred_queue, gt):
        by_weather[w][0].append(pd)
        by_weather[w][1].append(gt_)
    for w in sorted(by_weather):
        print(f"  weather={w:14s} queue_vs_gt {err_stats(*by_weather[w])}")

    q_rmse = err_stats(pred_queue, gt)["rmse"]
    if sum(pred_det) == 0:
        # Detector blind on this source (e.g. schematic renders vs a photo-
        # trained model): the error is domain gap, not interpolation error,
        # so the trigger cannot be read. Fix the source before deciding.
        print(f"hybrid-trigger: INCONCLUSIVE — detector blind "
              f"(pred total 0 vs gt mean {sum(gt)/len(gt):.2f}); trigger undecided")
    else:
        print(f"hybrid-trigger: queue RMSE {q_rmse} {'>' if q_rmse > 0.5 else '<='} 0.5 "
              f"({'FIRES — build frame-skip hybrid' if q_rmse > 0.5 else 'holds — interpolation stays'})")

    if args.out_csv:
        with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["frame", "gt", "pred_det", "pred_queue", "weather"])
            w.writerows(zip(names, gt, pred_det, pred_queue, weathers))
        print(f"wrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
