---
target: Adaptive Traffic Signal Timer Streamlit UI
total_score: 23
max_score: 40
na_heuristics: 
p0_count: 2
p1_count: 2
target_identity: "file:C:\\Users\\Admin\\OneDrive\\Desktop\\IDEA\\Adaptive-Traffic-Signal-Timer\\src\\adaptive_traffic\\ui"
timestamp: 2026-10-21T05-36-39Z
slug: src-adaptive-traffic-ui
---
# Impeccable Critique — Adaptive Traffic Signal Timer UI

Method: dual-agent (A: design review subagent · B: detector + browser evidence subagent)
Target: src/adaptive_traffic/ui (Streamlit, 6 pages / 9 tabs) · Mode: Operate · Surface: http://localhost:8503
Total score: 23/40 (Acceptable) · Audit: 10/20 (Acceptable)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Model badge + env always visible, but "Real-time Dashboard" shows np.random values that change on every interaction |
| 2 | Match System / Real World | 2 | overview.py:47 glosses mAP50 as "finds of 100" (wrong); overview.py:62 relabels same number as "% of vehicles" |
| 3 | User Control and Freedom | 2 | "Save Configuration" / "Save Webhook" / "Test EVP" print success for work that never happens (advanced.py:83,254,370) |
| 4 | Consistency and Standards | 2 | Two icon systems (7 SVG vs ~40 emoji) and two accent colors (#2563eb vs Streamlit #ff4b4b on every widget) |
| 5 | Error Prevention | 2 | 300s subprocess.run with no cancel/progress; st.metric delta slot carries plain labels |
| 6 | Recognition Rather Than Recall | 3 | Everything labelled, but proof table shows raw fixture IDs (x4way_aggressive_waterlogged) |
| 7 | Flexibility and Efficiency | 2 | 16-17 focusables before the sidebar nav; no deep links |
| 8 | Aesthetic and Minimalist Design | 2 | Red widgets fight the restrained palette; Before/After chart unreadable (3 of 4 series flat) |
| 9 | Error Recovery | 2 | "Fetch Live Weather" claims a live API connection then shows static 22C (advanced.py:133) |
| 10 | Help and Documentation | 3 | Inline explainers + methodology notes, but the one plain-English glossary line is factually wrong |
| **Total** | | **23/40** | **Acceptable** |

## Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | 2 | Caption text 2.3:1 (our MUTED x Streamlit 0.6 opacity); tabs/sliders #ff4b4b 3.16-3.3:1; focus ring absent on role=tab; 21-62 SVGs/view with no aria-hidden; h1->h3 gaps |
| 2 | Performance | 2 | Full rerun per widget change; _facts.py disk reads uncached; blocking 300s subprocess; 8-16 Altair toolbar buttons per view |
| 3 | Theming | 2 | theme.py tokens never reach Streamlit widget layer; no .streamlit/config.toml; no dark mode; 3 competing color sets |
| 4 | Responsive | 2 | At 390px the sidebar paints over the main column, 19 elements >=79% occluded; no reflow |
| 5 | Implementation Integrity | 2 | theme.py is a real system, unwired; US street names on a mumbai/surat product; no PRODUCT.md/DESIGN.md |
| **Total** | | **10/20** | **Acceptable** |

## Design Specificity Verdict

Half-authored, and the wrong half. Overview and Comparison are written for this product (Eye->Brain->Hands
metaphor overview.py:82-87; "Green = startup + sum(vehicles x headway)" live_demo.py:61; explicit DQN/Webster/Fuzzy
dormancy comparison.py:20-24). The other four pages would ship unchanged for another product: dashboard.py:72-75
demos US intersections while city profiles are mumbai/surat; dashboard.py:192 and metrics.py:44 print the same four
hardcoded numbers (12,450 gal / 124 tons / 30% faster / $46M) on two "different" pages; advanced.py:19-27 is the
canonical IoT-smart-city settings template.

Deterministic scan: 8-10 findings per view at every viewport, stable across repeats. Systemic: low-contrast on
caption text (every view, root cause theme.py:81 + Streamlit caption opacity) and side-tab on card() (theme.py:62).
Per-view: skipped-heading h1->h3 (5 of 6 views), #ff4b4b contrast (Live Demo 6, Settings 3), text-occlusion at 390px.

A and B agree: the design system exists in Python but is not the system the user sees. B caught what A missed: the
caption contrast regression is ours (MUTED x opacity), the side-tab rule is ours (card()), the h1->h3 gap is ours.

Visual overlay: injection succeeded in a fresh tab on every view; window.impeccableScan present, 0 page errors,
badges visible in C:\Temp\ui-qa\qa-b\fresh-view-*.png.

## What's Working

1. _facts.py - one truth loader feeding five surfaces (app.py:53, overview.py:54, comparison.py:118, metrics.py:30):
   all show the same 0.8477.
2. Live Demo never hides failure (live_demo.py:195-207): shells to scripts/demo_sgp.py, shows stdout, prints stderr on failure.
3. Comparison's candour: "Fixed time is the honest baseline we beat", "Incidents are model approximations".

## Priority Issues

### [P0] Unlabelled fabricated numbers, including one that contradicts a real one
Location: dashboard.py:191-197 (94.2% "System Accuracy"), dashboard.py:202-251, dashboard.py:162-167,262-289;
advanced.py:73-76 (EVP 96.2%), advanced.py:101-126 (static 22C "live" weather), advanced.py:163-191;
metrics.py:44-64.
Impact: 94.2% visibly contradicts the measured 84.8% in the sidebar badge 200px away.
Fix: demo_badge() helper in theme.py beside card(); page-level banner on Dashboard/Settings/Impact-Metrics;
re-source dashboard.py:191-197 from _facts or delete it (do not label 94.2%).
Command: /impeccable harden

### [P0] The Live Demo control panel is a decoy
Location: live_demo.py:42-60 (sliders/policy) vs live_demo.py:185-193 (actual command).
Evidence: run builds demo_sgp.py --city --max-frames 8 --closed-frames 3; scripts/demo_sgp.py:50-58 accepts no
density/speed/policy argument; live_demo.py:127 is 45*0.58 and :142 is *1.25 (constants); :63-64 checkboxes never read;
:27-28 copy promises a virtual 4-way intersection with configurable flows.
Impact: reviewer sets traffic, clicks Run, gets output that contradicts their settings with no error.
Fix: two buttons - "Simulate (illustration)" and "Run real pipeline on BMD-45 photos"; pass sliders through to
demo_sgp.py or delete them; retitle "Predicted Performance" -> "Measured band" and source 42% from the eval win range.
Command: /impeccable clarify

### [P1] The design system never reaches the widgets, and fails WCAG AA where it does not
Location: theme.py:9,70-85; app.py:22-29 (set_page_config without theme block); no .streamlit/config.toml in repo.
Evidence: Streamlit default #ff4b4b on every radio/checkbox/slider/selected tab/primary button. Selected tab label
3.30:1; slider value text 3.16:1. Focus ring blue on button/a/input (theme.py:79) but red glow on role=tab.
Caption text 2.3:1 because MUTED #64748b is dimmed by Streamlit 0.6 caption opacity.
Fix: .streamlit/config.toml with primaryColor=#2563eb, backgroundColor=#f8fafc, secondaryBackgroundColor=#ffffff,
textColor=#0f172a; extend focus rule to [role=tab], [role=radio], [data-testid=stSlider]; caption color #475569+.
Command: /impeccable colorize

### [P1] Settings reports success for work that never happens
Location: none of advanced.py:60-63,66-69,129-131,184-188,219-252,363-368 is read back.
Fake successes at advanced.py:83-85, :133-134, :254-255, :370-371. "Fetch Live Weather" asserts a live API
connection then shows static 22C.
Fix: banner "Specification of planned capabilities - not wired in this build"; change the four buttons to state what
they are, or wire them; delete DQN hyperparameters advanced.py:245-246.
Command: /impeccable harden

### [P2] Numbers don't render right, and two charts are unreadable
Location: st.metric third arg is the delta slot -> "up eval scenes", "up Sunny", "up Fixed" (metrics.py:30-33,
advanced.py:123-126, live_demo.py:144). model["speed"].split()[0] (overview.py:72, metrics.py:32) drops "fps".
metrics.py:79-81 number_input discarded. dashboard.py:214-228 shared 600-1600 axis hides 3 of 4 series.
metrics.py:195-205 gallons + tons + dollars on one axis.
Fix: captions via help= or card(); keep "fps"; delete the dead input; per-facet scales or index=100; split the
5-year chart into three panels.
Command: /impeccable typeset

### [P2] Structural a11y debt: heading gaps, 40 emoji vs 7 icons, 16 focusables before nav
Location: raw <h1 class='main-header'> + st.subheader() -> h1->h3 on 5 of 6 views; dashboard.py:175-176 emits h4 then
h2 inside a card; ~40 emoji in headings/tabs/metrics; 21-62 SVGs per view with no aria-hidden; 8 Altair toolbar
buttons per chart put nav 16-17 tab-presses away; no skip link; page_icon emoji; (c) 2024.
Fix: use theme.heading() for h2; aria-hidden="true" on decorative SVGs; hide Altair toolbars; skip link; drop emoji
for _ICONS.
Command: /impeccable polish

## Persona Red Flags

**Alex (power user)** - 17 tab presses to reach nav (8 Altair toolbar buttons + 4 heading anchors ahead of it);
changing city is a no-op visible on one page only (app.py:45-50 -> overview.py:98-109); "Reload Configuration" calls
st.rerun() and discards scroll position; no deep links; Dashboard random values change on every touch so two states
cannot be compared.

**Sam (accessibility)** - selected tab label 3.30:1, slider value text 3.16:1 (AA failures); focus ring invisible on
role=tab (4 absent Dashboard, 5 Settings); heading structure breaks h1->h3 and h4->h2; 62 decorative SVGs announced
with no aria-hidden; traffic-bar utilization encoded by color alone (dashboard.py:84-86), number only in a
mouse-hover tooltip (WCAG 1.4.1); green up-deltas invert meaning ("42% better" announced as increase, "up Sunny");
canvas-rendered dataframes with no accessible table.

**Jordan (non-technical reviewer)** - one number, two incompatible names (sidebar "0.8477 mAP50" vs Overview
"AI finds 84.8% of vehicles"); the plain-English glossary line overview.py:47 is factually wrong; proof table shows
fixture IDs; "$138,000,150 ROI" unlabeled until an info box at the very bottom; "Surat home turf (15/15)" headlines a
4-row table (_facts.py:62-64 counts 15, :94 filters to 4); Live Demo copy promises a virtual 4-way simulator but runs
a photo pipeline; Settings tab titles promise capabilities with no indication they are a spec sheet.

## Minor Observations

app.py:87 "(c) 2024" next to v1.0.0; app.py:89 Documentation link likely 404s; comparison.py:87,125-126 hardcodes
"19-75%" as a literal, defeating _facts.py's no-drift promise; _facts.py:32-33 speed/int8 are hardcoded strings never
read from disk while metadata.json says quantization=int8; theme.py:11 BAD defined and never used; dashboard.py:111
capacity rules dashed red = same colour as the over-capacity bar; comparison.py:96-110 11 tiny facets vs one grouped
bar; live_demo.py:42-45 symmetric default sliders (35/35) make the adaptive feature look inert on arrival;
overview.py:100-109 raw config keys with no labels; use_container_width deprecated.

## Questions to Consider

1. If the reviewer's only job is "does this actually work?", does a synthetic Dashboard earn its place - or would
   collapsing Dashboard + Impact Metrics into one Proof page (eval matrix, metadata.json provenance, run log) beat
   every other page combined?
2. Should the Live Demo's two incompatible promises become two named buttons - "Simulate (illustration)" and
   "Run real pipeline on BMD-45 photos"?
3. Is Settings for the reviewer or for the future? If the reviewer: mark the five tabs "planned - not implemented" and
   shrink the page to the one live thing (city tuning), trading surface area for credibility.
4. .streamlit/config.toml + replacing the 40 emoji with the existing 7 SVG icons would collapse most remaining visual
   inconsistency in one afternoon - worth doing before anything else?
