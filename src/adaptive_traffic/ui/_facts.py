"""Shared review-truth for UI pages (stdlib only — no engine imports).

Numbers come from disk (registry metadata + eval scorecards) with verified
fallbacks, so the dashboard can never drift from BENCHMARKS.md again.
Respects the dependency rule: UI reads files + config only.

Provenance: `overall` and `per_class` are read from the registry metadata file;
the win counts, wait band and decision latency are read from the eval
scorecards. `speed` and `int8` are bench results verified on this machine, not
file-backed - the UI labels them "bench" wherever they appear.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_META = REPO_ROOT / "models/registry/india-yolov8n-final/metadata.json"
SCORE_11 = REPO_ROOT / "evals/results/scorecard_1792164898.json"  # fresh 2026-10-16
SCORE_11_FALLBACK = REPO_ROOT / "evals/results/scorecard_1789305524.json"
SCORE_15 = REPO_ROOT / "evals/results/scorecard_1790419766.json"  # Surat card


def get_model_facts() -> dict:
    """Canonical detector truth. Fallbacks = verified 2026-10-16 values."""
    facts = {
        "name": "india-yolov8n-final",
        "overall": 0.8477,
        "per_class": {
            "car": 0.9189,
            "auto": 0.9171,
            "motorcycle": 0.8887,
            "bus": 0.846,
            "truck": 0.8294,
            "bicycle": 0.6859,
        },
        "train": "8 loops 0.7949->0.8293 + 5-lesson polish",
        "speed": "5.1-8.2 fps CPU fp32",
        "int8": "staged (KEEP by 0.0045), fp32 ships",
    }
    try:
        meta = json.loads(REGISTRY_META.read_text(encoding="utf-8"))
        facts["name"] = meta.get("name", facts["name"])
        facts["overall"] = meta.get("metrics", {}).get("mAP50_overall", facts["overall"])
        facts["per_class"] = meta.get("metrics", {}).get("per_class_mAP50", facts["per_class"])
    except (OSError, ValueError):
        pass
    facts["speed_short"] = facts["speed"].split(" CPU")[0]
    return facts


def get_eval_facts() -> dict:
    """Eval matrix truth: fresh 11-scenario + Surat 15-scenario cards."""
    facts = {
        "wins_11": "11/11",
        "wins_15": "15/15",
        "dec95": "<0.11 ms",
        "wall": "11.7s",
        "wait_band": "19-75%",
    }
    card = None
    for path in (SCORE_11, SCORE_11_FALLBACK):
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
            break
        except (OSError, ValueError):
            continue
    if card:
        results = card.get("results", [])
        wins = sum(1 for r in results if r.get("delta_wait_pct", 0) > 0)
        dec95 = max((r.get("adaptive", {}).get("dec_p95_ms", 0) for r in results), default=0)
        deltas = [r.get("delta_wait_pct", 0) for r in results]
        facts.update({"wins_11": f"{wins}/{len(results)}", "dec95": f"{dec95:.2f} ms"})
        if deltas:
            facts["wait_band"] = f"{min(deltas):.0f}-{max(deltas):.0f}%"
        facts["wall"] = f"{card.get('wall_s', 0):.1f}s"
    try:
        surat = json.loads(SCORE_15.read_text(encoding="utf-8")).get("results", [])
        wins = sum(1 for r in surat if r.get("delta_wait_pct", 0) > 0)
        facts["wins_15"] = f"{wins}/{len(surat)}"
    except (OSError, ValueError):
        pass
    return facts


def get_eval_table() -> dict:
    """Per-scenario adaptive-vs-fixed waits for the Comparison page."""
    out = {"fresh": [], "surat": []}
    fresh = []
    for path in (SCORE_11, SCORE_11_FALLBACK):
        try:
            fresh = json.loads(path.read_text(encoding="utf-8")).get("results", [])
            break
        except (OSError, ValueError):
            continue
    for r in fresh:
        out["fresh"].append(
            {
                "Scenario": r.get("name", "?"),
                "Adaptive (s)": r.get("adaptive", {}).get("avg_waiting_time", 0),
                "Fixed (s)": r.get("fixed", {}).get("avg_waiting_time", 0),
                "Win %": r.get("delta_wait_pct", 0),
            }
        )
    try:
        surat = json.loads(SCORE_15.read_text(encoding="utf-8")).get("results", [])
    except (OSError, ValueError):
        surat = []
    for r in surat:
        if "surat" in r.get("name", ""):
            out["surat"].append(
                {
                    "Scenario": r.get("name", "?"),
                    "Adaptive (s)": r.get("adaptive", {}).get("avg_waiting_time", 0),
                    "Fixed (s)": r.get("fixed", {}).get("avg_waiting_time", 0),
                    "Win %": r.get("delta_wait_pct", 0),
                }
            )
    return out
