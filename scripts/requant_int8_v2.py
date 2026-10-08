"""Re-quantize india-yolov8n-final to int8 WITHOUT touching the canonical registry.

Writes versioned candidates + parity report; promotes nothing.
Usage: .venv\\Scripts\\python.exe scripts/requant_int8_v2.py [--calib 200] [--eval-frames 20]
"""
import argparse, gc, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "models/registry/india-yolov8n-final/model.onnx"
OUTDIR = ROOT / "models/registry/india-yolov8n-final-candidates"
EVAL_DIR = ROOT / "data/trafficcam/images/val"


def build_calib_list(n=200, seed=42):
    import random
    rng = random.Random(seed)
    tc = sorted((ROOT / "data/trafficcam/images/val").glob("*.jpg"))
    syn_dense = sorted((ROOT / "data/synthetic_india_yolo/images/val").glob("*aggressive_metro*.jpg"))
    syn_rain = [p for p in sorted((ROOT / "data/synthetic_india_yolo/images/val").glob("*.jpg"))
                if "monsoon" in p.name or "waterlogged" in p.name or "rain" in p.name]
    # Stratified: 120 real + 50 dense + 30 rain (fall back gracefully if pools short)
    picks = tc[:120] + rng.sample(syn_dense, min(50, len(syn_dense))) + rng.sample(syn_rain, min(30, len(syn_rain)))
    while len(picks) < n:  # top up from trafficcam train-ish pools, never duplicate
        extra = [p for p in tc if p not in picks]
        if not extra:
            break
        picks.append(rng.choice(extra))
    cov = {"n": len(picks), "trafficcam_real": sum(1 for p in picks if "trafficcam" in str(p)),
           "synthetic_dense": sum(1 for p in picks if "aggressive_metro" in p.name),
           "rain_tags": sum(1 for p in picks if any(k in p.name for k in ("monsoon", "waterlogged", "rain")))}
    return picks[:n], cov


class Reader:
    def __init__(self, paths, input_name):
        import cv2
        import numpy as np
        self._cv2, self._np = cv2, np
        self.paths, self.input_name = list(paths), input_name
        self.enum = None

    def get_next(self):
        if self.enum is None:
            self.enum = iter(self.paths)
        p = next(self.enum, None)
        if p is None:
            return None
        img = self._cv2.imread(str(p))
        img = self._cv2.resize(img, (640, 640))
        img = self._cv2.cvtColor(img, self._cv2.COLOR_BGR2RGB).astype("float32") / 255.0
        return {self.input_name: self._np.ascontiguousarray(img.transpose(2, 0, 1)[None])}


def quantize_all(calib_paths, eval_frames):
    import onnxruntime as ort
    from onnxruntime.quantization import (QuantFormat, QuantType, CalibrationMethod,
                                          quant_pre_process,
                                          quantize_dynamic, quantize_static)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    META = str(ROOT / "models/registry/india-yolov8n-final/metadata.json")
    sess = ort.InferenceSession(str(SRC), providers=["CPUExecutionProvider"])
    iname = sess.get_inputs()[0].name
    del sess; gc.collect()  # free native heap: cv2 needs contiguous ~6MB per 1080p calib frame
    import onnx as _onnx
    tail = [n.name for n in list(_onnx.load(str(SRC)).graph.node)[-20:]]  # fp32 score/box tail: full-static mangles DFL+Sigmoid (v6, 2026-10-11)
    report = {"src": str(SRC), "eval_frames": [str(p) for p in eval_frames], "variants": {}}

    cfgs = {
        # Entropy histograms hold per-tensor state x N frames: cap at 100 to fit laptop RAM.
        "v1-static-entropy-qdq": dict(calibrate_method=CalibrationMethod.Entropy,
                                      quant_format=QuantFormat.QDQ,
                                      activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
                                      per_channel=True, calib_cap=100),
        "v2-static-minmax-qdq": dict(calibrate_method=CalibrationMethod.MinMax,
                                     quant_format=QuantFormat.QDQ,
                                     activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
                                     per_channel=True, calib_cap=None),
    }
    for tag, kw in cfgs.items():
        out = OUTDIR / f"model-{tag}.onnx"
        cap = kw.pop("calib_cap")
        paths = calib_paths[:cap] if cap else calib_paths
        pre = OUTDIR / f"_pre_{tag}.onnx"
        try:
            quant_pre_process(str(SRC), str(pre))
            quantize_static(str(pre), str(out), Reader(paths, iname), nodes_to_exclude=tail, **kw)
            ok, err = True, ""
        except Exception as e:  # noqa: BLE001
            ok, err = False, repr(e)[:300]
        report["variants"][tag] = {"path": str(out), "ok": ok, "error": err, **{k: str(v) for k, v in kw.items()}}

    out_dyn = OUTDIR / "model-v3-dynamic.onnx"
    try:
        quantize_dynamic(str(SRC), str(out_dyn), weight_type=QuantType.QInt8)
        report["variants"]["v3-dynamic"] = {"path": str(out_dyn), "ok": True, "error": ""}
    except Exception as e:  # noqa: BLE001
        report["variants"]["v3-dynamic"] = {"path": str(out_dyn), "ok": False, "error": repr(e)[:300]}

    # Non-degeneracy gate on identical real frames
    from adaptive_traffic.core.detection.adapters_onnx import OnnxDetector
    from footage import load_frames
    fs, _, _ = load_frames(str(EVAL_DIR), 20)
    for tag, v in report["variants"].items():
        if not v["ok"]:
            continue
        try:
            d = OnnxDetector(model_path=v["path"], metadata_path=META, confidence_threshold=0.25)
            counts = [len(d.detect(f).detections) for f in fs]
            v.update(det_total=sum(counts), zeros=sum(1 for c in counts if c == 0),
                     max_per_frame=max(counts), degenerate=(sum(counts) == 0))
        except Exception as e:  # noqa: BLE001
            v.update(ok=False, error="eval:" + repr(e)[:200])
    (OUTDIR / "requant_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: {kk: v[kk] for kk in ("ok", "det_total", "zeros", "max_per_frame", "degenerate", "error") if kk in v}
                      for k, v in report["variants"].items()}, indent=2))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", type=int, default=200)
    ap.add_argument("--eval-frames", type=int, default=20)
    a = ap.parse_args()
    t0 = time.time()
    calib, cov = build_calib_list(a.calib)
    print("calibration coverage:", json.dumps(cov))
    quantize_all(calib, sorted(EVAL_DIR.glob("*.jpg"))[: a.eval_frames])
    print(f"done in {time.time()-t0:.0f}s -> {OUTDIR}/requant_report.json")
