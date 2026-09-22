# Pull Request

## What (one line)


## Verification (paste results — AGENTS.md entry points only)

- [ ] `loop-fast`: `pytest tests/unit tests/integration -q -x --no-header -p no:cacheprovider` → ___ passed, ___ skipped
- [ ] `verify` (if touched beyond unit/integration scope): `pytest -q` → ___
- [ ] `eval` (if scheduler/policy/sim changed): 11/11 adaptive wins? ___ `dec_p95` regressions? ___
- [ ] `bench-*` (if perf-relevant): ___ → recorded in `docs/BENCHMARKS.md`
- [ ] Lint on touched graded paths: `black --check --line-length=100`, `isort --check-only --profile=black`, `flake8 --select=E9,F`

## Docs

- [ ] `docs/BENCHMARKS.md` updated (any benchmark run)
- [ ] `docs/MASTER_PLAN.md` §7 + changelog (any phase/decision change)
- [ ] No stale claims introduced (no int8-quality language without a verified artifact; test counts match)

## Notes for reviewers (tradeoffs, follow-ups)

