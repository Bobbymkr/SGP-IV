"""Unit tests for scripts/footage.py (Phase B helpers).

Pure helpers only — no model, no camera. Fast by design.
"""

import csv
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from footage import (  # noqa: E402
    det_hist,
    err_stats,
    load_frames,
    parse_weather,
    read_gt_csv,
    yolo_gt_counts,
)


@pytest.fixture()
def frames_dir(tmp_path):
    d = tmp_path / "frames"
    d.mkdir()
    for i, val in enumerate((10, 20, 30)):
        cv2.imwrite(str(d / f"f{i:03d}.jpg"), np.full((32, 32, 3), val, np.uint8))
    (d / "notes.txt").write_text("not an image")
    (d / "corrupt.jpg").write_bytes(b"not jpeg data")
    return d


def test_load_frames_sorted_skips_unreadable_and_limits(frames_dir):
    frames, names, skipped = load_frames(frames_dir)
    assert names == ["f000.jpg", "f001.jpg", "f002.jpg"]
    assert len(frames) == 3 and skipped == 1  # corrupt.jpg; notes.txt ignored by ext
    assert frames[0].shape == (32, 32, 3)
    # 'corrupt.jpg' sorts before 'f*.jpg', so max_frames=3 admits it (skipped)
    # plus the first two valid frames.
    frames, names, _ = load_frames(frames_dir, max_frames=3)
    assert names == ["f000.jpg", "f001.jpg"]


def test_det_hist_quantiles_and_empty():
    h = det_hist([0, 0, 1, 2, 5])
    assert (h["min"], h["max"], h["zeros"], h["n"]) == (0, 5, 2, 5)
    assert h["p50"] == 1 and h["p95"] == 5
    assert det_hist([])["n"] == 0


def test_parse_weather_tags_and_unknown():
    assert parse_weather("j17_noon_3way_heavy_monsoon_aggressive_f0001.jpg") == "heavy_monsoon"
    assert parse_weather("clip_light_rain_x.jpg") == "light_rain"
    assert parse_weather("phone_footage_001.jpg") == "unknown"


def test_err_stats_rmse_mae_bias():
    s = err_stats([0, 2, 4], [0, 0, 0])
    assert s == {"n": 3, "rmse": pytest.approx(2.582, abs=1e-3), "mae": 2.0, "bias": 2.0}
    assert err_stats([], [])["n"] == 0


def test_yolo_gt_counts_missing_file_is_zero(tmp_path):
    labels = tmp_path / "labels"
    labels.mkdir()
    (labels / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n1 0.2 0.2 0.05 0.05\n")
    (labels / "b.txt").write_text("\n")
    assert yolo_gt_counts(labels, ["a", "b", "c"]) == [2, 0, 0]


def test_read_gt_csv_hand_count_format(tmp_path):
    p = tmp_path / "ground_truth.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "count"])
        w.writerow(["clip_0001.jpg", 7])
        w.writerow(["clip_0002.jpg", 0])
    assert read_gt_csv(p) == {"clip_0001": 7, "clip_0002": 0}
