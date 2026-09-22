"""Closed-loop CI simulation (Phase C lab slice, Week-5 E2E without hardware).

  frames -> detect -> estimate -> decide(engine) -> actuate(STMP)

Default actuation is the Mock STMP adapter (lab-safe). Pass --ntcip-ip to aim
the SAME loop at a real controller later — no code change, that is the
hardware handoff. Exit 1 if any frame fails to actuate.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from footage import load_frames  # noqa: E402

from adaptive_traffic.adapters import create_ntcip_adapter  # noqa: E402
from adaptive_traffic.config.city_profile import get_city_profile  # noqa: E402
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator  # noqa: E402
from adaptive_traffic.core.closed_loop import create_loop, run_frame  # noqa: E402
from adaptive_traffic.core.detection.base import DetectorPort  # noqa: E402
from adaptive_traffic.core.pipeline import StagedPipeline  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames-dir", default=None)
    p.add_argument("--frames", type=int, default=20, help="synth-noise frames when no dir")
    p.add_argument("--max-frames", type=int, default=20)
    p.add_argument("--backend", default="onnx", choices=["ultralytics", "onnx", "tensorrt"])
    p.add_argument("--model", default="yolov8n.pt")
    p.add_argument("--registry", default="models/registry/india-yolov8n-final")
    p.add_argument("--city", default="bangalore")
    p.add_argument("--conf", type=float, default=0.45)
    p.add_argument("--ntcip-ip", default=None, help="real controller IP (default: mock)")
    p.add_argument("--ntcip-port", type=int, default=5000)
    args = p.parse_args()

    if args.frames_dir:
        frames, _, skipped = load_frames(args.frames_dir, args.max_frames)
        if not frames:
            print(f"no readable frames in {args.frames_dir}")
            return 1
        if skipped:
            print(f"warning: skipped {skipped} unreadable files")
        source = f"frames-dir:{args.frames_dir}"
    else:
        import numpy as np

        rng = np.random.default_rng(42)
        n = args.max_frames or args.frames
        frames = [rng.integers(0, 255, (640, 640, 3), dtype=np.uint8) for _ in range(n)]
        source = "synth-noise"

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

    profile = get_city_profile(args.city)
    pipe = StagedPipeline(detector, QueueEstimator(profile))
    sim, ix_id = create_loop(city_profile=profile)
    ntcip_cfg = {
        "ntcip_controller_ip": args.ntcip_ip or "127.0.0.1",
        "ntcip_stmp_port": args.ntcip_port,
        "ntcip_phase_mapping": {"north": 1, "south": 2, "east": 3, "west": 4},
        "ntcip_detector_mapping": {"1": "north", "2": "south", "3": "east", "4": "west"},
        "ntcip_transport": "both",
    }
    stmp = create_ntcip_adapter(ntcip_cfg, mock=args.ntcip_ip is None)

    fails, phases, t0 = 0, [], time.perf_counter()
    for i, f in enumerate(frames):
        r = run_frame(pipe, sim, ix_id, stmp, f)
        fails += not r["actuated"]
        phases.append(r["phase"])
        print(
            f"frame={i:4d} det={r['detected']:3d} queue={r['queued']:3d} "
            f"demands={r['demands']} phase={r['phase']:10s} "
            f"cycle={r['cycle_length']:.0f}s actuated={r['actuated']}"
        )
    wall = time.perf_counter() - t0
    served = sorted(set(phases))
    print(
        f"loop frames={len(frames)} source={source} backend={args.backend} "
        f"actuated={len(frames) - fails}/{len(frames)} phases_seen={served} "
        f"wall={wall:.1f}s stmp={'mock' if args.ntcip_ip is None else args.ntcip_ip}"
    )
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
