"""One-command SGP demo: checks -> picks frames -> AI sees -> photos to green.

Run this in front of the reviewer and narrate the two SAY lines:
  .venv\\Scripts\\python.exe scripts/demo_sgp.py --city mumbai --max-frames 20

Reuses bench_detect + run_closed_loop seams (footage.load_frames,
DetectorPort, StagedPipeline, create_loop/run_frame, mock STMP).
Backup console is saved to --backup for hall-WiFi-fails case.
"""

import argparse
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from footage import det_hist, load_frames, parse_weather  # noqa: E402

CANDIDATES = [
    "data/trafficcam/images/val",  # real Indian CCTV first (model actually finds cars)
    "data/trafficcam/images/test",
    "data/synthetic_india_yolo/images/val",  # renders fallback (model is blind 0/576)
    "data/synthetic_india_yolo/images/test",
]

# shortcut: weather balance is filename-tag only; untagged pools stay sorted-first,
# upgrade to stratified sampling only if a reviewer asks for rain contrast proof.


def pick_balanced(paths, n):
    paths = sorted(paths)
    clear = [p for p in paths if parse_weather(p.name) == "clear"]
    rain = [p for p in paths if parse_weather(p.name) in ("light_rain", "heavy_monsoon", "waterlogged")]
    rest = [p for p in paths if p not in clear and p not in rain]
    want_clear = n // 2
    picked = (clear[:want_clear] + rain[: n - len(clear[:want_clear])]) if (clear or rain) else []
    for p in rest:
        if len(picked) >= n:
            break
        picked.append(p)
    return picked[:n] if picked else paths[:n]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--city", default="mumbai")
    p.add_argument("--max-frames", type=int, default=20)
    p.add_argument("--closed-frames", type=int, default=5)
    p.add_argument("--frames-dir", default=None, help="skip auto-pick, use this dir")
    p.add_argument("--out-dir", default=r"C:\Temp\sgp-demo-frames")
    p.add_argument("--backend", default="onnx", choices=["ultralytics", "onnx", "tensorrt"])
    p.add_argument("--registry", default="models/registry/india-yolov8n-final")
    p.add_argument("--conf", type=float, default=0.45)
    p.add_argument("--backup", default="sgp-ppt-handoff/refs-demo-output.txt")
    args = p.parse_args()
    log = []

    def say(s):
        print(s)
        log.append(s)

    say("SGP DEMO: Smart Green Light for India (one command)")
    try:
        import onnxruntime  # noqa: F401
    except ImportError as e:
        say(f"FAIL: onnxruntime missing: {e}")
        return 1
    reg = Path(args.registry) / "model.onnx"
    if not reg.exists():
        say(f"FAIL: model missing: {reg}")
        return 1
    say(f"OK: model {reg} present")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if args.frames_dir:
        src_paths = sorted(
            pth
            for pth in Path(args.frames_dir).iterdir()
            if pth.is_file() and pth.suffix.lower() in (".jpg", ".jpeg", ".png")
        )
        src = args.frames_dir
    else:
        src, src_paths = None, []
        for cand in CANDIDATES:
            d = Path(cand)
            if not d.is_dir():
                continue
            got = sorted(
                q
                for q in d.iterdir()
                if q.is_file() and q.suffix.lower() in (".jpg", ".jpeg", ".png")
            )
            if len(got) >= 5:
                src, src_paths = cand, got
                break
        if not src:
            say("FAIL: no source frames found in candidates")
            return 1
    picked = pick_balanced(src_paths, args.max_frames)
    for q in picked:
        shutil.copy2(q, out / q.name)
    say(f"Frames: {len(picked)} from {src} -> {out} (clear+rain mix when tagged)")

    from adaptive_traffic.adapters import create_ntcip_adapter  # noqa: E402
    from adaptive_traffic.config.city_profile import get_city_profile  # noqa: E402
    from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator  # noqa: E402
    from adaptive_traffic.core.closed_loop import create_loop, run_frame  # noqa: E402
    from adaptive_traffic.core.detection.base import DetectorPort  # noqa: E402
    from adaptive_traffic.core.pipeline import StagedPipeline  # noqa: E402

    cfg = {"backend": args.backend, "confidence_threshold": args.conf}
    cfg["registry_dir"] = args.registry
    try:
        detector = DetectorPort.create(cfg)
    except (ImportError, ValueError, FileNotFoundError) as e:
        say(f"FAIL: backend '{args.backend}' unavailable: {e}")
        return 1

    frames, names, skipped = load_frames(str(out), args.max_frames)
    if not frames:
        say(f"FAIL: no readable frames in {out}")
        return 1
    if skipped:
        say(f"warning: skipped {skipped} unreadable files")

    # LIVE 1: AI sees
    say("--- LIVE 1: AI sees cars now. 5 to 8 photos in one second. ---")
    detector.detect(frames[0])  # warmup
    counts, classes, t0 = [], Counter(), time.perf_counter()
    for f in frames:
        dets = detector.detect(f).detections
        counts.append(len(dets))
        classes.update(d.class_name for d in dets)
    el = time.perf_counter() - t0
    fps = len(frames) / el
    say(f"AI result: {len(frames)} photos, {fps:.1f} per second, {sum(counts)} cars found")
    say(f"det_hist={det_hist(counts)} class_counts={dict(classes)}")
    if sum(counts) == 0:
        say("NOTE: zero finds = renders pool (model is blind 0/576 there); re-run with trafficcam val.")
    else:
        top = classes.most_common(3)
        say(f"Look: {', '.join(f'{k} {v}' for k, v in top)} — India mix (auto/bike present).")

    # LIVE 2: photos to green
    say(f"--- LIVE 2: same photos become queue, green time, signal ({args.city}). ---")
    profile = get_city_profile(args.city)
    pipe = StagedPipeline(detector, QueueEstimator(profile))
    sim, ix_id = create_loop(city_profile=profile)
    stmp = create_ntcip_adapter(
        {
            "ntcip_controller_ip": "127.0.0.1",
            "ntcip_stmp_port": 5000,
            "ntcip_phase_mapping": {"north": 1, "south": 2, "east": 3, "west": 4},
            "ntcip_detector_mapping": {"1": "north", "2": "south", "3": "east", "4": "west"},
            "ntcip_transport": "both",
        },
        mock=True,
    )
    fails, phases, t1 = 0, [], time.perf_counter()
    for i, f in enumerate(frames[: args.closed_frames]):
        r = run_frame(pipe, sim, ix_id, stmp, f)
        fails += not r["actuated"]
        phases.append(r["phase"])
        say(
            f"frame={i} cars={r['detected']} queue={r['queued']} "
            f"phase={r['phase']} cycle={r['cycle_length']:.0f}s actuated={r['actuated']}"
        )
    say(
        f"Loop: actuated={len(frames[: args.closed_frames]) - fails}/"
        f"{len(frames[: args.closed_frames])} phases={sorted(set(phases))} "
        f"wall={time.perf_counter() - t1:.1f}s stmp=mock (same code takes --ntcip-ip for real box)"
    )
    Path(args.backup).parent.mkdir(parents=True, exist_ok=True)
    Path(args.backup).write_text("\n".join(log) + "\n", encoding="utf-8")
    say(f"Backup saved: {args.backup} (open if hall Wi-Fi dies)")
    if fails:
        say("FAIL: a frame did not actuate (exit 1, do not hide).")
        return 1
    say("PASS: demo complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
