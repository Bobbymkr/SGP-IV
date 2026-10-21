---
target: Adaptive Traffic Signal Timer Streamlit UI
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 4
target_identity: "file:C:\\Users\\Admin\\OneDrive\\Desktop\\IDEA\\Adaptive-Traffic-Signal-Timer\\src\\adaptive_traffic\\ui"
timestamp: 2026-10-21T11-28-51Z
slug: src-adaptive-traffic-ui
---
# Impeccable Critique — Adaptive Traffic Signal Timer UI (final re-run)

Method: dual-agent (A: design review · B: detector + browser evidence)
Target: src/adaptive_traffic/ui (Streamlit, 6 pages / 9 tabs) · Mode: Operate
Total score: 28/40 (Good) — up from 23 → 25 · Detector: 8-10 → 0-1 per view

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Sidebar "last real run" badge now refreshes after a run; no timestamp on other numbers |
| 2 | Match System / Real World | 3 | Glossary + plain-English captions; raw scenario IDs still leak on the proof page |
| 3 | User Control and Freedom | 3 | Cancel / Run again / sliders all work; no way to clear the run history |
| 4 | Consistency and Standards | 3 | One design system, one accent; the measured strip repeats on four pages |
| 5 | Error Prevention | 3 | Inputs carry units; the unverifiable "9% of fuel burned" claim was removed |
| 6 | Recognition Rather Than Recall | 3 | Chips + sidebar badge; no measured number links to its source file |
| 7 | Flexibility and Efficiency | 2 | Evidence is session-only; no deep links, no result export, run knobs capped |
| 8 | Aesthetic and Minimalist Design | 3 | Restrained, dense, single accent; the measured strip repeats |
| 9 | Error Recovery | 3 | Pipeline path exemplary (Cancel, stdout+stderr always shown); the model path has no diagnostics |
| 10 | Help and Documentation | 3 | Glossary, inline help, methodology block, footer links; scenario IDs unexplained |
| **Total** | | **28/40** | **Good** |

## Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | 3 | Captions 7.24:1, selected tab 4.94:1, 0 elements without accessible name, radio focus ring added; charts still have no text alternative |
| 2 | Performance | 3 | 1 s fragment refresh, threaded run, no page block; charts have no data-table alternative |
| 3 | Theming | 4 | `.streamlit/config.toml` + one token set, one accent, no Streamlit red, Deploy hidden |
| 4 | Responsive | 3 | Sidebar collapses under 390 px (no occlusion), content reflows at 1100 px |
| 5 | Implementation Integrity | 3 | Truth grammar + India rate module with dated sources; run history still session-only |
| **Total** | | **16/20** | **Good** |

## Design Specificity Verdict

Authored for this product, not category-interchangeable: the three-value truth grammar
(MEASURED / ILLUSTRATION / SPEC), disk-backed measured numbers, India-native money and
quantity system with Indian digit grouping, and traffic-native vocabulary (NTCIP STMP,
J2735 SPAT, per-class detection gaps used to argue why emergency preemption cannot work).

Remaining generic layer: the Algorithm Overview pros/cons copy, stock Streamlit page
furniture, and the measured strip repeated on four pages.

## What's Working

1. The truth grammar is a real design system, not a label: a non-engineer can tell, unaided,
   which numbers are real, which are modelled, and which features are not built.
2. The pipeline genuinely runs and the simulation is genuinely walled off from it: a real run
   (8 photos, 52 cars, 3/3 actuated) with the page responsive, Cancel, and last-run + history.
3. India-native units with visible dates and sources, and a price that actually moves:
   switching the city changes the fuel price and every rupee figure that depends on it.
4. Colour discipline holds up: every token pair passes WCAG AA, one accent, status colours
   reserved, icons hand-built as aria-hidden SVG.

## Priority Issues (all fixed in the follow-up pass)

### [P1] The most-measured heading named a dataset the run never touched
"Real pipeline on BMD-45 photos" while the run output says `Frames: 8 from
data/trafficcam/images/val`.
FIXED: heading is now "Real pipeline on real traffic photos", the tagline says BMD-45 is the
training set, and the frame source is parsed from the run output and shown.

### [P1] The methodology stated a number the page itself refuted
"the fuel saved is about 9% of the fuel burned at that junction" cannot be verified without
an assumed trip length.
FIXED: the claim is gone; the note now states the volumes are per-intersection constants
scaled by the traffic figure and that converting them to a share of fuel burned needs a
trip-length assumption we have not made.

### [P1] Live Demo ended with a dead, contradictory duplicate section
A second "Real pipeline on BMD-45 photos" heading tagged ILLUSTRATION, empty, after the proof.
FIXED: deleted.

### [P1] Settings contradicted the honesty story: "Controller: dqn"
`settings.controller_type` is read by nothing, and Overview says the DQN stays dormant.
FIXED: the page now names the controller actually wired into eval and the closed loop
(adaptive weighted + clockwise, Green / Order / Cap) and marks the old setting as unused.

### [P2] Evidence access
Sidebar badge never refreshed after a run; run history is session-only; charts have no text
alternative; no number links to its source file.
FIXED (part): the badge refreshes (full rerun on run completion), the Comparison chart has a
text-version caption, the run history shows the frame source. Still open: persisting history
across refresh and per-chart data tables.

## Detector (final)

| Viewport | Findings |
|---|---|
| 1280x800 | 0 |
| 1500x950 | 1 (line-length, warning) |
| 390x844 | 0 |
| 1100x800 | 1 (straggler, advisory) |
| source scan | 0 (structural blindness proven with a control: inline HTML in .py is not parsed) |

False positives checked: 3 low-contrast 1.0:1 on the Live Demo slider thumb labels (the
detector resolves the thumb square as the label's background; the label sits above it on the
page background and really measures 4.89:1).
