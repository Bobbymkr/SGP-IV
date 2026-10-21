"""Runtime reader for configs/device.yaml (MASTER_PLAN D5).

profile_device.py WRITES active_tier; this module READS it. Unknown or
missing tier fails safe to low (CPU onnx-fp32 runs anywhere). `auto`
re-resolves via provider presence. Stdlib + pyyaml (already a dep).
"""

from pathlib import Path
from typing import Any, Dict, Tuple

REPO = Path(__file__).resolve().parents[3]
DEVICE_YAML = REPO / "configs" / "device.yaml"

TIERS = ("low", "mid", "high")


def read_tier(path: Path = DEVICE_YAML) -> Tuple[str, Dict[str, Any]]:
    """Return (tier, detection-config dict). Never raises on bad config."""
    try:
        import yaml

        raw = yaml.safe_load(open(path, encoding="utf-8")) or {}
    except (OSError, ValueError):
        raw = {}
    tier = str(raw.get("active_tier", "low")).lower()
    if tier == "auto":
        tier = _detect()
    if tier not in TIERS:
        tier = "low"  # ponytail: fail safe, don't fail loud on a review box
    det = (raw.get("detection") or {}).get(tier) or {}
    return tier, {
        "backend": det.get("backend", "onnx"),
        **{k: v for k, v in det.items() if k != "backend"},
    }


def _detect() -> str:
    try:
        import onnxruntime

        providers = onnxruntime.get_available_providers()
    except ImportError:
        return "low"
    if "TensorrtExecutionProvider" in providers:
        return "high"
    if "CUDAExecutionProvider" in providers:
        return "mid"
    return "low"
