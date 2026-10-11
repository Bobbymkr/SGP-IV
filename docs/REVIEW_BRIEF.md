# Review Brief — Adaptive Traffic Signal Timer

Source: `scorecard_1790419766.json` (15 scenarios, wall 24.19s).
Regenerate: `python scripts/review_brief.py`. Incidents are synthetic
approximations (see scorecard notes), not field events.

## Claims x evidence

| Claim | Result |
|---|---|
| Adaptive beats fixed-time everywhere | **15/15** |
| Surat profile wins on home turf | **4/15** |
| Incidents degrade gracefully, never lose | **5/15** |
| Decide stays real-time (p95 < 10 ms) | **15/15** |

## Scenario table (avg wait s, adaptive vs fixed)

| Scenario | City | Adapt | Fixed | Win % |
|---|---|---|---|---|
| x4way_clear_disciplined | default | 4.94 | 6.66 | 25.83 |
| x4way_clear_aggressive | default | 4.68 | 8.89 | 47.36 |
| x3way_typical_clear | default | 4.05 | 8.65 | 53.18 |
| x5way_typical_clear | default | 14.32 | 54.28 | 73.62 |
| x4way_typical_light_rain | default | 12.47 | 19.1 | 34.71 |
| x4way_typical_heavy_monsoon | default | 12.67 | 28.32 | 55.26 |
| x4way_typical_waterlogged | default | 21.93 | 47.44 | 53.77 |
| x4way_aggressive_waterlogged | default | 22.16 | 29.75 | 25.51 |
| x5way_aggressive_monsoon | default | 23.92 | 96.66 | 75.25 |
| x4way_sensor_failure | default | 21.93 | 47.44 | 53.77 |
| x4way_lane_block | default | 8.47 | 10.49 | 19.26 |
| x4way_surat_typical | surat | 18.2 | 30.88 | 41.06 |
| x4way_surat_rally | surat | 13.31 | 19.66 | 32.3 |
| x4way_surat_cattle | surat | 22.87 | 31.71 | 27.88 |
| x4way_surat_vip | surat | 36.03 | 47.93 | 24.83 |

**15/15 adaptive wins.**
