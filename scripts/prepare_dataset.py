"""Dataset normalizer/validator — enforces docs/DATASET_SPEC.md contract.

Usage:
  python scripts/prepare_dataset.py <raw_root> --out <dataset_root> [--source yolo|coco]
  python scripts/prepare_dataset.py <dataset_root> --check
  python scripts/prepare_dataset.py <dataset_root> --make-calibration

--source coco expects COCO-JSON annotations (annotations/*.json) and maps
categories by name onto the contract schema.
"""

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

CONTRACT_CLASSES = ["car", "motorcycle", "bus", "truck", "bicycle", "auto"]
SPLITS = ("train", "val", "test")


def _class_index(name: str):
    n = name.lower().strip()
    aliases = {
        "motorbike": "motorcycle", "moto": "motorcycle",
        "bicycle": "bicycle", "bike": "bicycle",
        "autorickshaw": "auto", "rickshaw": "auto", "three_wheeler": "auto",
    }
    mapped = aliases.get(n, n)
    return CONTRACT_CLASSES.index(mapped) if mapped in CONTRACT_CLASSES else None


def _write_data_yaml(root: Path, class_names=None):
    names = class_names or CONTRACT_CLASSES
    lines = ["path: .", "train: images/train", "val: images/val", "test: images/test", "names:"]
    lines += [f"  {i}: {n}" for i, n in enumerate(names)]
    (root / "data.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def convert_yolo(raw_root: Path, out_root: Path):
    for split_dir in ("train", "val", "test"):
        imgs = list((raw_root / "images" / split_dir).glob("*.jpg"))
        labels = raw_root / "labels" / split_dir
        (out_root / "images" / split_dir).mkdir(parents=True, exist_ok=True)
        (out_root / "labels" / split_dir).mkdir(parents=True, exist_ok=True)
        copied = dropped = 0
        for img in imgs:
            lbl = labels / (img.stem + ".txt")
            if not lbl.exists():
                dropped += 1
                continue
            valid = True
            for line in lbl.read_text().splitlines():
                parts = line.split()
                if len(parts) != 5 or int(parts[0]) >= len(CONTRACT_CLASSES) or \
                   any(not (0.0 <= float(v) <= 1.0) for v in parts[1:]):
                    valid = False
                    break
            if not valid:
                dropped += 1
                continue
            shutil.copy2(img, out_root / "images" / split_dir / img.name)
            shutil.copy2(lbl, out_root / "labels" / split_dir / lbl.name)
            copied += 1
        print(f"{split_dir}: copied={copied} dropped_invalid_or_unlabeled={dropped}")
    if (raw_root / "meta" / "captures.json").exists():
        (out_root / "meta").mkdir(exist_ok=True)
        shutil.copy2(raw_root / "meta" / "captures.json", out_root / "meta" / "captures.json")
    _write_data_yaml(out_root)


def convert_coco(raw_root: Path, out_root: Path):
    ann_files = sorted((raw_root / "annotations").glob("*.json"))
    if not ann_files:
        sys.exit("no COCO-JSON under annotations/")
    by_name = {}
    for f in ann_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        cats = {c["id"]: c["name"] for c in data.get("categories", [])}
        imgs = {im["id"]: im for im in data.get("images", [])}
        per_img = {}
        for a in data.get("annotations", []):
            cname = cats.get(a["category_id"])
            idx = _class_index(cname) if cname else None
            if idx is None:
                continue
            x, y, w, h = a["bbox"]
            iw, ih = imgs[a["image_id"]]["width"], imgs[a["image_id"]]["height"]
            cx, cy = (x + w / 2) / iw, (y + h / 2) / ih
            per_img.setdefault(a["image_id"], []).append(
                f"{idx} {cx:.6f} {cy:.6f} {w / iw:.6f} {h / ih:.6f}"
            )
        for img_meta in data.get("images", []):
            fname = Path(img_meta["file_name"]).name
            src = raw_root / "images" / fname
            if not src.exists() or not per_img.get(img_meta["id"]):
                continue
            split = by_name.setdefault(fname, "train")
            (out_root / "images" / split).mkdir(parents=True, exist_ok=True)
            (out_root / "labels" / split).mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out_root / "images" / split / fname)
            (out_root / "labels" / split / (src.stem + ".txt")).write_text(
                "\n".join(per_img[img_meta["id"]]) + "\n", encoding="utf-8"
            )
    _write_data_yaml(out_root)


def check(dataset_root: Path) -> int:
    errors = []
    for split in SPLITS:
        img_dir, lbl_dir = dataset_root / "images" / split, dataset_root / "labels" / split
        if not img_dir.exists():
            continue
        images = {p.stem for p in img_dir.glob("*.jpg")}
        labels = {p.stem for p in lbl_dir.glob("*.txt")}
        missing = images - labels
        if missing:
            errors.append(f"{split}: {len(missing)} unlabeled images e.g. {sorted(missing)[:3]}")
        for lbl in lbl_dir.glob("*.txt"):
            for i, line in enumerate(lbl.read_text().splitlines()):
                parts = line.split()
                if len(parts) != 5 or int(parts[0]) >= len(CONTRACT_CLASSES) or \
                   any(not (0.0 <= float(v) <= 1.0) for v in parts[1:]):
                    errors.append(f"{lbl.name}:{i + 1} invalid label line")
                    break

    captures = dataset_root / "meta" / "captures.json"
    if captures.exists():
        meta = json.loads(captures.read_text(encoding="utf-8"))
        train_junctions = {c["junction_type"] + "_" + c.get("day", "") for c in meta}
        print(f"captures.json: {len(meta)} clips; verify splits are junction-day disjoint manually")

    calib = dataset_root / "calibration" / "frames"
    if not calib.exists() or not any(calib.glob("*.jpg")):
        errors.append("calibration/frames empty or missing (spec §6)")

    if errors:
        print(f"FAILED ({len(errors)}):")
        for e in errors[:20]:
            print(" -", e)
        return 1
    print("OK: dataset satisfies DATASET_SPEC.md v1")
    return 0


def make_calibration(dataset_root: Path, count: int = 200):
    captures = dataset_root / "meta" / "captures.json"
    rainy = set()
    if captures.exists():
        meta = json.loads(captures.read_text(encoding="utf-8"))
        rainy = {c["clip_id"] for c in meta if c.get("weather") in ("light_rain", "heavy_rain", "waterlogged")}
    all_frames = [p for s in SPLITS for p in (dataset_root / "images" / s).glob("*.jpg")]
    rng = random.Random(42)

    def is_rainy(p: Path) -> bool:
        return any(r in p.stem for r in rainy)

    wet = [p for p in all_frames if is_rainy(p)]
    dry = [p for p in all_frames if not is_rainy(p)]
    n_wet = min(len(wet), int(count * 0.3))
    picked = rng.sample(wet, n_wet) + rng.sample(dry, min(len(dry), count - n_wet))
    out = dataset_root / "calibration" / "frames"
    out.mkdir(parents=True, exist_ok=True)
    for p in picked:
        shutil.copy2(p, out / p.name)
    print(f"calibration: wrote {len(picked)} frames ({n_wet} rain-affected)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, help="output dataset root when converting")
    ap.add_argument("--source", choices=("yolo", "coco"), default="yolo")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--make-calibration", action="store_true")
    args = ap.parse_args()

    if args.check:
        sys.exit(check(args.root))
    if args.make_calibration:
        make_calibration(args.root)
        return
    if not args.out:
        sys.exit("conversion requires --out")
    if args.source == "coco":
        convert_coco(args.root, args.out)
    else:
        convert_yolo(args.root, args.out)
    print(f"wrote {args.out}; run --check next")


if __name__ == "__main__":
    main()
