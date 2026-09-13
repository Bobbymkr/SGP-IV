"""Dataset normalizer/validator — enforces docs/DATASET_SPEC.md contract.

Usage:
  python scripts/prepare_dataset.py <raw_root> --out <dataset_root> [--source yolo|coco|voc] [--option A|B]
  python scripts/prepare_dataset.py <dataset_root> --check
  python scripts/prepare_dataset.py <dataset_root> --make-calibration

--source coco expects COCO-JSON annotations (annotations/*.json) and maps
categories by name onto the contract schema.
--source voc expects Pascal VOC XML annotations (one *.xml per image with
<filename>, <size>, and <object>/<bndbox> tags) and maps category names onto
the contract schema. Used for the IITM-HeTra_v2 pilot from the kalyan1729
traffic-management dataset.
"""

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

CONTRACT_CLASSES = ["car", "motorcycle", "bus", "truck", "bicycle", "auto"]
SPLITS = ("train", "val", "test")


# Option B (aggressive merge): Bengaluru fine-grained classes folded onto the
# 6-class contract. Same class ids — no DATASET_SPEC schema change required.
# Rationale: visual similarity at CCTV distance; keeps every id stable.
MERGE_B = {
    # car-like passenger vehicles
    "sedan": "car", "hatchback": "car", "suv": "car", "muv": "car",
    # bus-like people carriers
    "minibus": "bus", "mini_bus": "bus", "van": "bus",
    "tempo_traveller": "bus", "tempo": "bus",
    # truck-like goods carriers
    "lcv": "truck",
}


def _class_index(name: str, option: str = "A"):
    n = name.lower().strip().replace(" ", "_").replace("-", "_")
    aliases = {
        "motorbike": "motorcycle", "moto": "motorcycle",
        "two_wheeler": "motorcycle",
        "bicycle": "bicycle", "bike": "bicycle",
        "autorickshaw": "auto", "rickshaw": "auto",
        "three_wheeler": "auto", "auto_rickshaw": "auto",
    }
    if option == "B":
        aliases.update(MERGE_B)
    # Option A (conservative): only the 6 exact contract class names pass;
    # anything else returns None and is dropped by callers.
    mapped = aliases.get(n, n)
    return CONTRACT_CLASSES.index(mapped) if mapped in CONTRACT_CLASSES else None


def _has_split_images(root: Path, split: str) -> bool:
    d = root / "images" / split
    return d.is_dir() and any(d.glob("*.jpg"))


def _write_data_yaml(root: Path, class_names=None):
    names = class_names or CONTRACT_CLASSES
    root.mkdir(parents=True, exist_ok=True)
    # NOTE: ultralytics resolves a relative `path:` against the process CWD,
    # not the yaml's directory — so always write the absolute dataset root.
    # If a split has no images (e.g. HeTra ships train/test only), point val
    # at test so `yolo train`/`val` never crash on a missing dir.
    val = (
        "images/val"
        if _has_split_images(root, "val")
        else ("images/test" if _has_split_images(root, "test") else "images/train")
    )
    lines = [
        f"path: {root.resolve()}",
        "train: images/train",
        f"val: {val}",
        "test: images/test",
        "names:",
    ]
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


def convert_coco(raw_root: Path, out_root: Path, option: str = "A"):
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
            idx = _class_index(cname, option) if cname else None
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


def _load_voc_splits(raw_root: Path) -> dict:
    """Load IITM-HeTra-style trainval/test membership. Returns {stem: split}.

    Searches recursively because HF layouts nest the lists (e.g.
    IITM-HeTra_v2/Dataset-1/trainval.txt). Strips a UTF-8 BOM from each line
    so files written on Windows (PowerShell's default UTF-8-with-BOM) still
    match VOC <filename> stems.
    """
    membership: dict = {}
    for split_name, list_files in (
        ("train", ("trainval.txt", "train.txt")),
        ("val", ("val.txt",)),
        ("test", ("test.txt",)),
    ):
        for lf in list_files:
            for lp in sorted(raw_root.rglob(lf)):
                for raw in lp.read_text(encoding="utf-8").splitlines():
                    stem = raw.strip().lstrip("\ufeff")
                    if stem:
                        membership[stem] = split_name
    return membership


def convert_voc(raw_root: Path, out_root: Path, option: str = "A"):
    """Pascal VOC XML -> contract. Expects <img>.jpg + <img>.xml in the same tree.

    Walks raw_root for *.xml files, parses <filename>/<size>/<object><bndbox>,
    and writes YOLO-format labels. Unknown category names are dropped
    (conservative Option A). IITM-HeTra-style trainval/test lists are honored
    if present; otherwise everything lands in train.
    """
    import xml.etree.ElementTree as ET

    xmls = sorted(raw_root.rglob("*.xml")) + sorted(raw_root.rglob("*.XML"))
    if not xmls:
        sys.exit("no VOC XML files found under raw_root")

    # IITM-HeTra-style layouts keep xmls/ and images/ in SEPARATE dirs, so
    # index every image under raw_root by stem for fallback resolution.
    img_index: dict = {}
    for pat in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"):
        for p in raw_root.rglob(pat):
            img_index.setdefault(p.stem, p)

    membership = _load_voc_splits(raw_root)
    n_with_boxes = 0
    n_dropped_class = 0
    n_missing_img = 0
    for xml_path in xmls:
        try:
            tree = ET.parse(xml_path)
        except ET.ParseError:
            continue
        root = tree.getroot()

        size = root.find("size")
        if size is None:
            continue
        try:
            w = int(size.findtext("width") or 0)
            h = int(size.findtext("height") or 0)
        except ValueError:
            continue
        if w <= 0 or h <= 0:
            continue

        img_path = None
        path_text = root.findtext("path")
        if path_text and Path(path_text).exists():
            img_path = Path(path_text)
        if img_path is None:
            fn = root.findtext("filename") or xml_path.stem
            for cand in (
                xml_path.parent / fn,  # image next to the XML
                xml_path.with_suffix(".jpg"),
                img_index.get(Path(fn).stem),  # separate images/ dir
                img_index.get(xml_path.stem),
            ):
                if cand is not None and cand.exists():
                    img_path = cand
                    break
        if img_path is None:
            n_missing_img += 1
            continue

        yolo_lines = []
        for obj in root.findall("object"):
            cname = obj.findtext("name")
            idx = _class_index(cname, option) if cname else None
            if idx is None:
                n_dropped_class += 1
                continue
            bb = obj.find("bndbox")
            if bb is None:
                continue
            try:
                xmin = float(bb.findtext("xmin"))
                ymin = float(bb.findtext("ymin"))
                xmax = float(bb.findtext("xmax"))
                ymax = float(bb.findtext("ymax"))
            except (TypeError, ValueError):
                continue
            bw, bh = xmax - xmin, ymax - ymin
            if bw <= 0 or bh <= 0:
                continue
            cx = (xmin + bw / 2) / w
            cy = (ymin + bh / 2) / h
            yolo_lines.append(f"{idx} {cx:.6f} {cy:.6f} {bw / w:.6f} {bh / h:.6f}")

        if not yolo_lines:
            continue

        split = membership.get(img_path.stem, "train")

        (out_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_root / "labels" / split).mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_path, out_root / "images" / split / img_path.name)
        (out_root / "labels" / split / (img_path.stem + ".txt")).write_text(
            "\n".join(yolo_lines) + "\n", encoding="utf-8"
        )
        n_with_boxes += 1

    if n_with_boxes == 0:
        sys.exit(
            "voc: wrote 0 images — check raw_root layout (expected VOC *.xml files). "
            f"Top-level entries: {[p.name for p in sorted(raw_root.iterdir())][:10]}"
        )
    print(f"voc: wrote {n_with_boxes} images; dropped {n_dropped_class} objects (class not in Option A schema); {n_missing_img} xmls without matching image")
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
    ap.add_argument("--source", choices=("yolo", "coco", "voc"), default="yolo")
    ap.add_argument("--option", choices=("A", "B"), default="A",
                    help="A: exact 6-class match only; B: merge Bengaluru fine-grained classes")
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
        convert_coco(args.root, args.out, args.option)
    elif args.source == "voc":
        convert_voc(args.root, args.out, args.option)
    else:
        convert_yolo(args.root, args.out)
    print(f"wrote {args.out}; run --check next")


if __name__ == "__main__":
    main()
