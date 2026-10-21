"""One-page review brief from the latest eval scorecard (Part 3).

Usage: python scripts/review_brief.py [--scorecard <path>] [--out docs/REVIEW_BRIEF.md]
Regenerable by design: numbers always match the scorecard, never hand-copied.
"""

import argparse
import glob
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CLAIMS = [
    ("Adaptive beats fixed-time everywhere", lambda r: r["delta_wait_pct"] > 0),
    ("Surat profile wins on home turf", lambda r: r["city"] == "surat" and r["delta_wait_pct"] > 20),
    ("Incidents degrade gracefully, never lose", lambda r: "synthetic-approx" in r["incident_model"] and r["delta_wait_pct"] > 0),
    ("Decide stays real-time (p95 < 10 ms)", lambda r: r["adaptive"]["dec_p95_ms"] < 10),
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scorecard", default=None)
    p.add_argument("--out", default="docs/REVIEW_BRIEF.md")
    args = p.parse_args()

    sc = args.scorecard or max(
        glob.glob(str(REPO / "evals" / "results" / "scorecard_*.json")), key=os.path.getmtime
    )
    d = json.load(open(sc))
    rows = d["results"]
    wins = sum(1 for r in rows if r["delta_wait_pct"] > 0)

    lines = [
        "# Review Brief — Adaptive Traffic Signal Timer",
        "",
        f"Source: `{Path(sc).name}` ({len(rows)} scenarios, wall {d.get('wall_s', '?')}s).",
        "Regenerate: `python scripts/review_brief.py`. Incidents are synthetic",
        "approximations (see scorecard notes), not field events.",
        "",
        "## Claims x evidence",
        "",
        "| Claim | Result |",
        "|---|---|",
    ]
    for claim, pred in CLAIMS:
        got = sum(1 for r in rows if pred(r))
        lines.append(f"| {claim} | **{got}/{len(rows)}** |")
    lines += [
        "",
        "## Scenario table (avg wait s, adaptive vs fixed)",
        "",
        "| Scenario | City | Adapt | Fixed | Win % |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        a, f = r["adaptive"], r["fixed"]
        lines.append(
            f"| {r['name']} | {r['city']} | {a['avg_waiting_time']} | "
            f"{f['avg_waiting_time']} | {r['delta_wait_pct']} |"
        )
    lines += ["", f"**{wins}/{len(rows)} adaptive wins.**", ""]
    out = REPO / args.out
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({wins}/{len(rows)} wins)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
