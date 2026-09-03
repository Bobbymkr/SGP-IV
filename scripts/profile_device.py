"""Hardware tier profiler — detects capability and writes active_tier to
configs/device.yaml (MASTER_PLAN D5). Tiers: low (CPU-only), mid (GPU/NPU fp32),
high (Jetson-class with TensorRT).

ponytail: tiers decided by provider presence, not device model lists.
Re-run after driver/runtime changes.
"""

import argparse
import re
import sys
from pathlib import Path

DEVICE_YAML = Path(__file__).resolve().parents[1] / "configs" / "device.yaml"


def detect_tier() -> tuple[str, list[str]]:
    try:
        import onnxruntime
        providers = onnxruntime.get_available_providers()
    except ImportError:
        providers = ["CPUExecutionProvider"]

    has_cuda = "CUDAExecutionProvider" in providers
    has_trt = "TensorrtExecutionProvider" in providers

    if has_trt:
        return "high", providers
    if has_cuda:
        return "mid", providers
    return "low", providers


def write_tier(tier: str, path: Path = DEVICE_YAML) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^active_tier:\s*\S+", f"active_tier: {tier}", text, count=1, flags=re.M)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write detected tier to configs/device.yaml")
    parser.add_argument("--tier", choices=["low", "mid", "high"], help="Force a tier instead of detecting")
    args = parser.parse_args()

    tier, providers = (args.tier, []) if args.tier else detect_tier()
    print(f"tier: {tier}")
    if providers:
        print(f"onnxruntime providers: {', '.join(providers)}")
    if tier == "high":
        print("note: TensorRT adapter pending (falls back to ONNX); "
              "trt_cache_dir will fill on first on-device build")

    if args.write:
        write_tier(tier)
        print(f"wrote active_tier={tier} to {DEVICE_YAML}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
