---
target: Adaptive Traffic Signal Timer Streamlit UI
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 4
target_identity: "file:C:\\Users\\Admin\\OneDrive\\Desktop\\IDEA\\Adaptive-Traffic-Signal-Timer\\src\\adaptive_traffic\\ui"
timestamp: 2026-10-21T07-59-52Z
slug: src-adaptive-traffic-ui
---
# Impeccable Critique — Adaptive Traffic Signal Timer UI (re-run, post-fix)

Method: dual-agent (A: design review · B: detector + browser evidence)
Target: src/adaptive_traffic/ui (Streamlit, 6 pages / 9 tabs) · Mode: Operate
Total score: 25/40 (Acceptable) — up from 23/40 · Detector: 8-10 findings -> 0-2

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | No "last run" timestamp anywhere; pipeline output is lost on navigation |
| 2 | Match System / Real World | 2 | "Real-time Dashboard" titles a seeded RNG; mAP50/p95/SPAT/eval matrix ship unglossed |
| 3 | User Control and Freedom | 3 | Sidebar, tabs, CSV download all work; 60s run has no cancel and no history |
| 4 | Consistency and Standards | 2 | Three truth languages (chip / st.success / st.info); one alert colour for all alert types |
| 5 | Error Prevention | 2 | Model registry is free text with no validation; API tab documented auth that does not exist |
| 6 | Recognition Rather Than Recall | 3 | Sidebar badge and "Config in effect" help; proof reachable only via prose |
| 7 | Flexibility and Efficiency | 2 | No keyboard shortcuts, no deep links, no run history, no copy-paste command |
| 8 | Aesthetic and Minimalist Design | 2 | Impact Metrics = 4 measured + 4 modelled + 2 inputs + 8 charts in one scroll |
| 9 | Error Recovery | 3 | Failure path is good ("never hidden", stderr, backup) but the error text renders dark green |
| 10 | Help and Documentation | 3 | Inline captions, methodology box, API examples, Docs/Proof-pack links |
| **Total** | | **25/40** | **Acceptable** |

## Design Specificity Verdict

Authored for this product on the truth half (chip system, disk-backed fact loader, "Config in
effect", 4-step explainer, pinned palette, zero emoji) but the presentation half is a template
(cards, 4-across metric row, donut, 90-day trend line). The differentiator is expressed as a
12px pill while the generic scaffolding gets 36px headings.

## What's Working

1. The truth-chip system (chip/tagline/banner) is consistent and every MEASURED value reconciles
   with the artifacts on disk: 11/11 wins, 19-75% band, 0.10 ms dec p95, 0.8477 mAP50, 15/15 Surat.
2. "Config in effect" before a 60s black-box run is exemplary — it echoes city/confidence/
   registry/backend/photos and states the sliders are not involved.
3. Restraint in the chrome: one accent, slate ink, aria-hidden SVGs, zero emoji, no Altair toolbar.

## Priority Issues (all fixed in the follow-up pass)

### [P0] API tab misdescribed the API
Documented `Authorization: Bearer YOUR_API_KEY` while the API has no auth dependency, and the
route table omitted 11 served routes.
FIXED: auth section now states there is no authentication in this build; the Authorization
header is gone from both client examples; the table lists all 35 served routes; the drift test
now asserts both directions (tests/unit/test_ui_api_routes.py).

### [P1] Cross-page truth contradictions
Dashboard banner said proof was on Comparison while its own Performance tab carried measured
cards; Impact Metrics claimed "30% faster" emergency response that Settings says is not
implemented; Overview glossed int8 as shipping while the card said fp32 ships; the
Configuration chip claimed nothing was display-only while showing read-only defaults; the
Weather tab claimed hardcoded scene names came from the scorecards.
FIXED: every sentence reconciled — banner reworded, EVP card now says "Not in this build",
caption reworded, engine defaults moved under a SPEC chip, rain scenes derived from the scorecard.

### [P1] Impact Metrics: a wrong number and an invented one
`total_co2 * 22` cars-equivalent was ~100x inflated (409,200 cars vs 27 per 124 tons);
"ROI" was annual value x 3 with no cost basis; four projected sections carried no truth chip;
the note said $51/ton while the model used $50.
FIXED: cars use 27/124, the card is "3-year value ... not ROI", ILLUSTRATION chips added to the
projected sections, one carbon price used by both chart and note.

### [P1] Bar charts were stacked
Both the comparison chart and the Before/After chart stacked two independent measurements, so
the axis showed sums (x5way reached ~120 = 23.92 + 96.66) and the After bar appeared above
Before.
FIXED: xOffset added to both, so the bars are grouped.

### [P2] Accessibility gaps
Code blocks measured 2.65-3.83:1 (Streamlit dark-theme tokens on light); traffic chart encoded
severity by colour only with the legend removed; the 300px sidebar covered 79% of the content
at 390px; live-demo queue chart used two same-hue area fills.
FIXED: token colours overridden to AA values, colour key added as a caption, sidebar state set
to "auto" so it collapses on narrow screens, queue chart uses two distinct hues with strokes.

## Minor Observations

- st.success used as a data display creates a second truth language next to the chips.
- One metric renders three ways (0.8477 / 84.8% / 0.8477) with no anchor tying them together.
- registry/metadata.json still says "quantization": "int8" while the UI (correctly) ships fp32.
- "Adaptive policy pipeline wins in all 11/11 measured scenes" is redundant with wins_11.
- 17 "Link to heading" anchors enter the tab order with identical accessible names (framework).
- _facts.py speed and int8 strings are hand-typed while every other fact is disk-backed.
- The API snippet is Windows-only.
- Streamlit chrome (Deploy, main menu) reads as "prototype" to a reviewer.
