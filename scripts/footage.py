"""Shared footage helpers for bench_detect.py / score_queue.py (Phase B).

Small, dependency-free (numpy + stdlib; cv2 only inside load_frames):
- load_frames: sorted disk frames (BGR, matching OnnxDetector._preprocess)
- det_hist: per-frame count summary (min/p50/p95/max/zeros)
- parse_weather: weather tag from synthetic filenames (clear|light_rain|...)
- err_stats: RMSE / MAE / mean-bias of pred-vs-gt counts
- yolo_gt_counts / read_gt_csv: two ground-truth sources (labels dir for
  rendered sets, hand-count CSV for phone footage with no labels)
"""

import csv
import re
from pathlib import Path

import numpy as np

WEATHERS = ("clear", "light_rain", "heavy_monsoon", "waterlogged")
_WEATHER_RE = re.compile(r"_(clear|light_rain|heavy_monsoon|waterlogged)_")


def load_frames(frames_dir, max_frames=0, exts=("jpg", "jpeg", "png")):
    """Load frames sorted by name. Returns (frames, names, skipped).

    Unreadable files are skipped (counted), never fatal — a field SD card
    always has a few corrupt writes and the bench must survive them.
    """
    import cv2

    exts = {e.lower().lstrip(".") for e in exts}
    paths = sorted(
        p for p in Path(frames_dir).iterdir()
        if p.is_file() and p.suffix.lower().lstrip(".") in exts
    )
    if max_frames and max_frames > 0:
        paths = paths[:max_frames]
    frames, names, skipped = [], [], 0
    for p in paths:
        img = cv2.imread(str(p))
        if img is None:
            skipped += 1
            continue
        frames.append(img)
        names.append(p.name)
    return frames, names, skipped


def det_hist(counts):
    """Per-frame count summary. Empty input -> zeros (honest, not NaN)."""
    counts = [int(c) for c in counts]
    if not counts:
        return {"n": 0, "min": 0, "p50": 0, "p95": 0, "max": 0, "zeros": 0}
    s = sorted(counts)
    pick = lambda q: s[min(len(s) - 1, int(q * len(s)))]
    return {
        "n": len(s),
        "min": s[0],
        "p50": pick(0.5),
        "p95": pick(0.95),
        "max": s[-1],
        "zeros": sum(1 for c in s if c == 0),
    }


def parse_weather(filename):
    """Weather tag from synthetic clip filenames; 'unknown' for phone footage."""
    m = _WEATHER_RE.search(filename or "")
    return m.group(1) if m else "unknown"


def err_stats(pred, gt):
    """RMSE / MAE / mean-bias(pred-gt) over paired count lists."""
    pred = np.asarray(list(pred), dtype=float)
    gt = np.asarray(list(gt), dtype=float)
    if pred.size == 0:
        return {"n": 0, "rmse": 0.0, "mae": 0.0, "bias": 0.0}
    err = pred - gt
    return {
        "n": int(pred.size),
        "rmse": round(float(np.sqrt(np.mean(err**2))), 3),
        "mae": round(float(np.mean(np.abs(err))), 3),
        "bias": round(float(np.mean(err)), 3),
    }


def yolo_gt_counts(labels_dir, stems):
    """Ground-truth counts from YOLO label files (missing file == 0 objects)."""
    labels_dir = Path(labels_dir)
    out = []
    for stem in stems:
        p = labels_dir / f"{stem}.txt"
        if not p.exists():
            out.append(0)
            continue
        out.append(sum(1 for line in p.read_text().splitlines() if line.strip()))
    return out


def read_gt_csv(csv_path):
    """Hand-count ground truth: CSV with `frame,count` header. Returns dict."""
    gt = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            gt[Path(row["frame"]).stem] = int(row["count"])
    return gt
