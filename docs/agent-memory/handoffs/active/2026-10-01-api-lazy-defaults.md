# 2026-10-01 — API lazy defaults + bounds + readiness honesty

Goal: green `loop-fast`. Done: 99 passed, 1 skipped, 6.81s.
Claims: none open.

## Changed (root cause: routes stale after refactors, tests encode spec)

- `tests/unit/test_eval_runner.py` — `_midrun_step`/vip_hold/rally_block taxonomy gone from
  `evals/runner.py`; tests now cover `_apply_incident` (lane_block 0.3x, sensor_failure
  waterlogged) + `run_scenario` smoke.
- `src/adaptive_traffic/api/routes/signals.py` — `_get_or_create` lazy default; POST timing
  bounds `[min_green_time, max_green_time]` → 422, `last_timing`/`updated_at` set, queues
  untouched (was: 404 on unknown, 500 via `signal.last_updated`, green times into queues).
- `src/adaptive_traffic/api/routes/health.py` — readiness reports `{models, tier}` from
  `configs/device.yaml` + registry dir check; `ready`/`degraded`, no phantom db/redis.

## Next — done 2026-10-01

- `make verify` equiv: `pytest -q` → 106 passed, 1 skipped (31.98s); `flake8` → 486
  (== pre-change baseline; my 2 long lines trimmed, `signals.py:353,367` pre-existing).
- `make eval` equiv: `python evals/runner.py` → 11/11 adaptive wins, delta 19.3–75.2%,
  adaptive `dec_p95_ms` 0.12–0.70 « 10ms budget. Note: AGENTS.md `dec95_a ≤ 0.08`
  figure looks stale vs current ms-scale output — confirm before gating on it.
- First MCP downloads still pending: `npx -y sqlite-memory-mcp`, `codebase-memory-mcp cli index`.
