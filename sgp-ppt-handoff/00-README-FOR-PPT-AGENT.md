# Handoff to PPT Agent — Adaptive Traffic Signal Timer (SGP Review)

## Who you are
You are excellent at making PPT. Build a 12-slide deck for a college SGP review. Audience understands only simple English (A1-A2 level). Time: 15-20 min + 2-min live demo talk.

## Repo root
All paths below are relative to repo root `Adaptive-Traffic-Signal-Timer/`. Do NOT invent numbers. Use ONLY numbers in `01-PROJECT-FACTS.md`. If a number is missing, write `TBD` — never guess.

## Goals (must meet both)
1. Simple-language presentation — 1 idea per slide, short sentences, picture > words.
2. Development proofs — reviewer must see what is Planned / Developed / Tested / Ready-to-test / Hardware-gated.

## Reviewer lens (think like reviewer)
- Problem in 1 line? Why India?
- What did you build? Frame -> green flow?
- Proof it works? Numbers + live demo?
- What is done vs pending? Honest limits?
- Next step?

## Build order
1. Read `01-PROJECT-FACTS.md` (exact numbers), `02-SLIDES-DRAFT-A1A2.md` (slide text + speaker notes), `03-PROOF-INDEX.md` (claim -> file:line + status matrix).
2. Build 12 slides exactly in the order of `02-SLIDES-DRAFT-A1A2.md`. Keep titles as given.
3. Visual rules: big diagram on slides 3 and 8 (frame-to-green flow from `docs/ARCHITECTURE.md:21-35`); bar chart on slide 11 (adaptive vs fixed wait); table on slide 4 (per-class mAP50); status matrix table on slide 12 appendix or slide 6.
4. Language rules: A1-A2. Max 30 words per slide body. No jargon without a picture or 5-word explanation. Example: `mAP50 = correct finds out of 100`.
5. Honesty rules (non-negotiable): slide 12 MUST list: fp32 ships / int8 staged, incidents are synthetic-approx, no live camera yet, no real controller yet. Do NOT hide bicycle weak tail (0.6859).
6. Output: PPTX 16:9 + PDF export + `speaker-notes.txt` (copy notes from `02-SLIDES-DRAFT-A1A2.md`).

## Screenshots you can use (already captured, no need to re-run)
`sgp-ppt-handoff/ui-screens/` — 9 PNGs of the real dashboard at 1500px:
`01-overview`, `02-dashboard-traffic`, `03-dashboard-performance`, `04-dashboard-alerts`,
`05-live-demo`, `06-comparison`, `07-impact-metrics`, `08-settings-configuration`, `09-settings-api`.
Best slide material: `03-dashboard-performance` (measured cards), `06-comparison` (the proof
table + chart), `07-impact-metrics` (rupee projections with the dated rates line),
`05-live-demo` (the real run output).

## Dashboard facts you may quote
- Every number in the UI is tagged MEASURED / ILLUSTRATION / SPEC - the deck should say the same.
- Impact Metrics shows litres, rupees and tonnes, priced with 21 Oct 2026 Indian rates
  (petrol Rs 111.21/L Mumbai, 1 USD = Rs 94.77, carbon Rs 8,150/t per IISD).
  The quantities are modelled - say "modelled", never "measured".

## Existing starter (reuse, do not contradict)
- `sgp-presentation-pack/07-slides-outline.md` — 12-slide timing plan
- `sgp-presentation-pack/TRACE.md` — claim -> source
- `docs/demo-deck/bmd-finale.html` — old deck to extend, not replace
- `docs/ARCHITECTURE.md:12-35` — Mermaid diagrams to redraw as PPT graphics

## Demo slides (9-10) — mark as LIVE
- Slide 9: `python scripts/bench_detect.py --frames-dir <20 frames> --max-frames 20` → 5-8 fps CPU expected. Full runbook in `sgp-presentation-pack/06-demo-RUNBOOK.md`.
- Slide 10: `python scripts/run_closed_loop.py --frames-dir <same> --max-frames 5 --city mumbai` → queue → green → mock STMP.
- Add small footer on both: `Backup: pre-run output + bmd-finale.html if hall Wi-Fi dies`.

## What to deliver back
- `SGP-Review-Deck.pptx`, `SGP-Review-Deck.pdf`, `speaker-notes.txt`
- Reply with: slide count, words per slide check, list of any TBD you could not fill.

## Do NOT do
- Do NOT add new model numbers, new fps claims, or new eval wins.
- Do NOT add pedestrian phases, MARL results, or real-controller claims — they are deferred/gated (see `03-PROOF-INDEX.md`).
- Do NOT re-train anything or edit `src/`, `configs/`, `models/`.
