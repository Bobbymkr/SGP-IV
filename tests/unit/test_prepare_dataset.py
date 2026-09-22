"""Regression tests for scripts/prepare_dataset.py VOC path (Option A pilot).

Locks in two real bugs found during the IITM-HeTra pilot setup:
1. split lists nested one level down (Dataset-1/*.txt) were ignored, so every
   image defaulted to train;
2. UTF-8-BOM list files (PowerShell default) never matched VOC stems.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from prepare_dataset import (  # noqa: E402
    _class_index,
    _load_voc_splits,
    check,
    convert_trafficcam,
    convert_voc,
    make_calibration,
)

VOC_XML = """<annotation>
  <size><width>800</width><height>600</height></size>
  <object><name>{cls}</name><bndbox><xmin>10</xmin><ymin>20</ymin>
  <xmax>110</xmax><ymax>120</ymax></bndbox></object>
</annotation>
"""


@pytest.fixture()
def voc_raw(tmp_path: Path) -> Path:
    d = tmp_path / "Dataset-1"
    d.mkdir()
    (d / "keep.jpg").touch()
    (d / "keep.xml").write_text(VOC_XML.format(cls="auto_rickshaw"), encoding="utf-8")
    (d / "drop.jpg").touch()
    (d / "drop.xml").write_text(VOC_XML.format(cls="sedan"), encoding="utf-8")
    # BOM-prefixed on purpose: PowerShell Set-Content writes UTF-8-with-BOM.
    (d / "trainval.txt").write_bytes(b"\xef\xbb\xbfkeep\n")
    (d / "test.txt").write_bytes(b"\xef\xbb\xbfdrop\n")
    return tmp_path


def test_option_a_keeps_auto_drops_sedan(voc_raw: Path, tmp_path: Path):
    out = tmp_path / "out"
    convert_voc(voc_raw, out)
    assert (out / "images" / "train" / "keep.jpg").exists()
    assert not (out / "images" / "train" / "drop.jpg").exists()
    # class 5 == auto
    assert (out / "labels" / "train" / "keep.txt").read_text().startswith("5 ")


@pytest.fixture()
def voc_split_dirs(tmp_path: Path) -> Path:
    """IITM-HeTra-style layout: xmls/ and images/ in SEPARATE dirs."""
    d = tmp_path / "Dataset-1"
    (d / "xmls").mkdir(parents=True)
    (d / "images").mkdir(parents=True)
    (d / "images" / "frame_1.jpg").touch()
    (d / "xmls" / "frame_1.xml").write_text(VOC_XML.format(cls="car"), encoding="utf-8")
    (d / "images" / "frame_2.jpg").touch()
    (d / "xmls" / "frame_2.xml").write_text(VOC_XML.format(cls="bus"), encoding="utf-8")
    (d / "trainval.txt").write_text("frame_1\n", encoding="utf-8")
    (d / "test.txt").write_text("frame_2\n", encoding="utf-8")
    return tmp_path


def test_split_dirs_layout_resolves_images(voc_split_dirs: Path, tmp_path: Path):
    out = tmp_path / "out"
    convert_voc(voc_split_dirs, out)
    assert (out / "images" / "train" / "frame_1.jpg").exists()
    assert (out / "labels" / "train" / "frame_1.txt").exists()


def test_split_lists_honored_despite_bom(voc_raw: Path):
    membership = _load_voc_splits(voc_raw)
    assert membership == {"keep": "train", "drop": "test"}


def test_contract_check_passes_after_calibration(voc_raw: Path, tmp_path: Path):
    out = tmp_path / "out"
    convert_voc(voc_raw, out)
    make_calibration(out, count=1)
    assert check(out) == 0


def test_data_yaml_uses_abspath_and_val_fallback(voc_split_dirs: Path, tmp_path: Path):
    """ultralytics resolves `path: .` against CWD; val falls back to test."""
    out = tmp_path / "out"
    convert_voc(voc_split_dirs, out)
    text = (out / "data.yaml").read_text(encoding="utf-8")
    assert f"path: {out.resolve()}" in text
    assert "val: images/test" in text  # fixture has train/test only


def test_convert_coco_option_b_merge(tmp_path: Path):
    import json as _json

    from prepare_dataset import convert_coco

    raw = tmp_path / "raw"
    (raw / "annotations").mkdir(parents=True)
    (raw / "images").mkdir(parents=True)
    (raw / "images" / "f1.jpg").touch()
    (raw / "images" / "f2.jpg").touch()
    coco = {
        "categories": [
            {"id": 1, "name": "Sedan"},
            {"id": 2, "name": "LCV"},
            {"id": 3, "name": "Person"},
        ],
        "images": [
            {"id": 1, "file_name": "f1.jpg", "width": 100, "height": 100},
            {"id": 2, "file_name": "f2.jpg", "width": 100, "height": 100},
        ],
        "annotations": [
            {"image_id": 1, "category_id": 1, "bbox": [10, 10, 20, 20]},
            {"image_id": 2, "category_id": 2, "bbox": [10, 10, 20, 20]},
            {"image_id": 2, "category_id": 3, "bbox": [10, 10, 20, 20]},
        ],
    }
    (raw / "annotations" / "a.json").write_text(_json.dumps(coco), encoding="utf-8")
    out = tmp_path / "out"
    convert_coco(raw, out, option="B")
    # Sedan->car(0) kept, LCV->truck(3) kept, Person dropped; f2 has a kept box
    assert (out / "labels" / "train" / "f1.txt").read_text().startswith("0 ")
    assert (out / "labels" / "train" / "f2.txt").read_text().startswith("3 ")
    # Option A would drop both Sedan and LCV
    out_a = tmp_path / "out_a"
    convert_coco(raw, out_a, option="A")
    assert not (out_a / "images" / "train" / "f1.jpg").exists()
    assert not (out_a / "images" / "train" / "f2.jpg").exists()


def test_convert_voc_fails_fast_on_empty(tmp_path: Path):
    raw = tmp_path / "empty"
    raw.mkdir()
    (raw / "stray.txt").write_text("no xml here", encoding="utf-8")
    with pytest.raises(SystemExit):
        convert_voc(raw, tmp_path / "out")


def test_class_index_aliases():
    assert _class_index("auto_rickshaw") == 5
    assert _class_index("three-wheeler") == 5
    assert _class_index("two-wheeler") == 1  # aligned with probe notebook
    assert _class_index("sedan") is None  # Option A: dropped
    assert _class_index("tempo_traveller") is None  # Option A: dropped
    # TrafficCAM census aliases (ground truth 2026-09-21)
    assert _class_index("LMV") == 0
    assert _class_index("MotorBike") == 1
    assert _class_index("Motor Bike") == 1
    assert _class_index("Moterbike") == 1
    assert _class_index("e-rickshaw") == 5
    assert _class_index("Tractor") is None  # Option A: dropped (B merges to truck)


def test_option_b_merge_mapping():
    assert _class_index("sedan", "B") == 0
    assert _class_index("Hatchback", "B") == 0
    assert _class_index("SUV", "B") == 0
    assert _class_index("MUV", "B") == 0
    assert _class_index("Mini-bus", "B") == 2
    assert _class_index("Van", "B") == 2
    assert _class_index("Tempo-traveller", "B") == 2
    assert _class_index("LCV", "B") == 3
    assert _class_index("Tractor", "B") == 3
    assert _class_index("Two-wheeler", "B") == 1
    assert _class_index("Bicycle", "B") == 4
    assert _class_index("Three-wheeler", "B") == 5
    # Person stays dropped even under B (no pedestrian phase, D7)
    assert _class_index("Person", "B") is None
    assert _class_index("unknown-thing", "B") is None
    # Option A default unchanged
    assert _class_index("sedan") is None
    assert _class_index("LCV") is None


@pytest.fixture()
def trafficcam_raw(tmp_path: Path) -> Path:
    """Two video dirs: bbox JSON, polygon+RLE JSONs. Dims inline (no cv2)."""
    import json as _json

    raw = tmp_path / "raw"
    v1 = raw / "BLR_clip01"
    v1.mkdir(parents=True)
    for stem in ("frame0", "frame2"):
        (v1 / f"{stem}.jpg").touch()
    (v1 / "frame0.json").write_text(
        _json.dumps(
            {
                "imageWidth": 720,
                "imageHeight": 480,
                "objects": [
                    {"category": "car", "bbox": [10, 20, 100, 100]},
                    {"category": "Person", "bbox": [0, 0, 10, 10]},
                ],
            }
        ),
        encoding="utf-8",
    )
    (v1 / "frame2.json").write_text(
        _json.dumps(
            {
                "imageWidth": 720,
                "imageHeight": 480,
                "objects": [
                    {"category": "bus", "segmentation": [[10, 20, 110, 20, 110, 120, 10, 120]]},
                ],
            }
        ),
        encoding="utf-8",
    )
    v2 = raw / "DEL_clip02"
    v2.mkdir(parents=True)
    (v2 / "frame0.jpg").touch()
    # 4x4 mask, foreground cols/rows 1-2 -> bbox (1,1,2,2)
    (v2 / "frame0.json").write_text(
        _json.dumps(
            {
                "imageWidth": 4,
                "imageHeight": 4,
                "objects": [
                    {
                        "category": "motor",
                        "segmentation": {"counts": [5, 2, 2, 2, 5], "size": [4, 4]},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    # labelme-style point list: [[x,y],...] must box all points (regression:
    # an early branch read these as zero-area boxes and wrote 0 frames)
    v3 = raw / "HYD_clip03"
    v3.mkdir(parents=True)
    (v3 / "frame0.jpg").touch()
    (v3 / "frame0.json").write_text(
        _json.dumps(
            {
                "version": "5.0.1",
                "imageHeight": 100,
                "imageWidth": 200,
                "shapes": [
                    {"label": "MotorBike", "points": [[10, 10], [30, 10], [30, 50], [10, 50]]},
                ],
            }
        ),
        encoding="utf-8",
    )
    return raw


def test_trafficcam_geometries_and_video_split_hygiene(trafficcam_raw: Path, tmp_path: Path):
    out = tmp_path / "out"
    convert_trafficcam(trafficcam_raw, out, option="B")
    labels = list((out / "labels").rglob("*.txt"))
    assert len(labels) == 4  # frame0+frame2 of v1, frame0 of v2/v3
    # bbox path: car(0) kept, Person dropped
    f0 = next(p for p in labels if p.stem == "BLR_clip01_frame0")
    assert f0.read_text().splitlines() == ["0 0.083333 0.145833 0.138889 0.208333"]
    # polygon path: bus(2), (10,20,110,120) on 720x480
    f2 = next(p for p in labels if p.stem == "BLR_clip01_frame2")
    assert f2.read_text().splitlines() == ["2 0.083333 0.145833 0.138889 0.208333"]
    # RLE path: motor->motorcycle(1), (1,1,2,2) on 4x4
    fr = next(p for p in labels if p.stem == "DEL_clip02_frame0")
    assert fr.read_text().splitlines() == ["1 0.375000 0.375000 0.250000 0.250000"]
    # labelme path: MotorBike->motorcycle(1), points box (10,10,30,50) on 200x100
    fl = next(p for p in labels if p.stem == "HYD_clip03_frame0")
    assert fl.read_text().splitlines() == ["1 0.100000 0.300000 0.100000 0.400000"]
    # whole videos in one split each (no temporal leak)
    splits = {p.parent.name for p in labels if p.stem.startswith("BLR_clip01")}
    assert len(splits) == 1
    caps = __import__("json").loads((out / "meta" / "captures.json").read_text())
    assert {c["clip_id"] for c in caps} == {"BLR_clip01", "DEL_clip02", "HYD_clip03"}
    assert {c["city"] for c in caps} == {"BLR", "DEL", "HYD"}


def test_trafficcam_fails_fast_on_empty(tmp_path: Path):
    raw = tmp_path / "empty"
    raw.mkdir()
    (raw / "stray.txt").write_text("no json here", encoding="utf-8")
    with pytest.raises(SystemExit):
        convert_trafficcam(raw, tmp_path / "out")
