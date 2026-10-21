# 02 — 12-Slide Draft in A1-A2 English (use titles verbatim)

## Slide 1 — Title (30s)
Title: Smart Green Light for India
Body: Adaptive Traffic Signal Timer. AI watches cars and gives smart green time. For Indian roads.
Visual: 1 junction photo + project name + team/date placeholders [TBD team names].
Say: `Hello. Our project makes green lights smart for Indian traffic.`

## Slide 2 — The Problem (1:30)
Title: The Problem: Fixed Green Wastes Time
Body: Fixed green time is unfair. Bikes, autos, buses share one road. Rain makes it worse. 3-way, 4-way, 5-way crossings are different.
Visual: 3 small photos: mixed traffic / monsoon / 5-way sketch.
Say: `One green time for all roads wastes time. Indian roads are mixed and rainy.`

## Slide 3 — Our Idea (1:00)
Title: Our Idea: Camera to Green
Body: Camera sees cars. AI counts queue. Brain chooses green. Signal changes.
Visual: Redraw flow from `docs/ARCHITECTURE.md:12-19`: Cameras -> AI detects -> Queue -> Green -> Less waiting.
Say: `Camera to AI to queue to green. That is the full system.`

## Slide 4 — The AI Eye (2:00)
Title: The AI Eye: 85 of 100 Cars Found
Body: YOLOv8n, India-tuned. Full test 10,000 photos: 84.77%. Car 92, Auto 92, Bike 89, Bus 85, Truck 83, Cycle 69. Cycle is weak — we show it.
Visual: Table of 6 classes + 1 miss-frame placeholder (bicycle at night).
Say: `Our AI finds 85 of 100 vehicles. Small cycle is hard. We are honest about it.`

## Slide 5 — How We Taught It (3:00)
Title: How We Taught It: Contract, Loops, Polish
Body: Step 1: One data contract for all sources. Step 2: 8 learning loops, 79 to 83. Step 3: Final polish, 5 lessons, 84.77.
Visual: 3 boxes with arrows + scores 0.7949 -> 0.8293 -> 0.8477.
Say: `Same contract, many loops, small final polish. Full 10k test, no cherry-pick.`

## Slide 6 — Why 6 Vehicle Types (1:30)
Title: Why 6 Types: India Is Mixed
Body: Car, bike, bus, truck, cycle, auto. Auto and bike are many in India. Each has its own length and green need.
Visual: 6 icons with lengths (car 4.5m, bus 12m, auto 3m, bike 2m).
Say: `We keep auto and bike separate. They move different.`

## Slide 7 — Made for Indian Cities (2:00)
Title: Made for Mumbai, Delhi, Bangalore
Body: Mumbai: 4 lanes, auto+bike heavy, rain mode, green 15-90s. Change city = change file. No code change.
Visual: Mini table Mumbai/Delhi/Bangalore (lanes, behavior, weather) from `docs/ARCHITECTURE.md:160-166`.
Say: `Mumbai is busy and rainy. Settings change by city file.`

## Slide 8 — Live Flow: Frame to Green (2:00)
Title: Live Flow: Frame to Green in Milliseconds
Body: Detect 5-8 photos per second. Decide green in 2 ms. Slow AI never blocks the queue. Sends to signal box + cars.
Visual: Pipeline diagram: Detector (5-8 fps) -> Queue -> Green/Order/Cap (p95 <3ms) -> STMP/SPAT.
Say: `AI is fast. Brain is faster. Old frames are dropped, never block.`

## Slide 9 — LIVE Demo 1: AI Sees (1:30) [mark LIVE badge]
Title: LIVE: AI Sees Cars Now
Body: Command + expected: 20 photos, 5-8 fps CPU, counts per type. Zero-find would show, not hide.
Visual: Screenshot placeholder of `bench_detect` console output.
Say: `Watch. Same AI, real Indian photos, on normal CPU.`

## Slide 10 — LIVE Demo 2: Full Loop (1:00) [mark LIVE badge]
Title: LIVE: Photos to Green to Signal
Body: Same photos -> queue -> green -> mock signal box. Same code can talk to real box with one IP flag.
Visual: Screenshot placeholder of `run_closed_loop --city mumbai` output (cycle 61-66s breathing).
Say: `Photos become green time and go to the signal.`

## Slide 11 — Proof: We Always Win (1:30)
Title: Proof: Smart Beats Fixed, 15 of 15 Times
Body: Wait down 19% to 75%. 5-way best: 14s vs 54s. Surat rally -32%, cattle -28%, VIP -25%. Brain <0.1 ms.
Visual: Bar chart adaptive (short) vs fixed (tall) for 5 rows: x3way, x5way, monsoon, rally, VIP. Footnote: incidents are model approximations, not field events.
Say: `Smart always wins. Big crossings win most. Tests are models, we label them.`

## Slide 12 — Honest Gaps and Next (1:00)
Title: Honest Gaps and Next Steps
Body: NOW: fp32 ships, int8 staged (miss by 0.0045). No live camera yet. No real box yet. NEXT: phone video test, Jetson test, verified int8.
Visual: 3-column table Done / Ready-to-test / Needs hardware (copy from `03-PROOF-INDEX.md` status matrix, 5 rows max).
Say: `We show what works and what is next. Small fast model and live road test are next.`

## Appendix A (not presented unless asked) — Status matrix full + file refs
## Appendix B — Glossary: mAP50 = correct finds of 100; int8 = small fast model; STMP = signal-box language; SPAT = signal message to cars.
