# Test Cleanup Log — 2026-09-18 (Phase A: kill stale tests)

Commit before cleanup: `0cd889a` (`feat(detection): tensorrt adapter via ORT TRT-EP — Phase 5 done`).
Net diff of this cleanup: **~2,982 deletions / ~30 insertions** across 10 paths.

## Why this file exists

Every deletion below is recorded with its pre-delete blob hash and an exact
restore command, so any entry can be recovered from git history for reference
without resurrecting it into the live suite.

## Whole-file deletions (6)

| File | Size | Lines | Blob (pre-delete) | Reason | Restore |
|------|------|-------|-------------------|--------|---------|
| `tests/unit/test_vehicle_detection_unit.py` | 18,657 B | 473 | `e8463a93fa96fb1d0c28ac7dfca6faf9eeb56a44` | Targets deleted `Code/YOLO/darkflow` `vehicle_detection_modern` module; was ignore-globbed in `conftest.py`, never ran | `git show e8463a93fa96fb1d0c28ac7dfca6faf9eeb56a44 > /tmp/restore_vehicle_detection_unit.py` |
| `tests/unit/test_simulation_unit.py` | 25,581 B | 561 | `1291bf8d0e375356c7e04467a74b03c959368ac4` | Targets deleted darkflow `simulation` module (`defaultRed`, `TrafficSignal`, pygame `Vehicle`); was ignore-globbed, never ran | `git show 1291bf8d0e375356c7e04467a74b03c959368ac4 > /tmp/restore_simulation_unit.py` |
| `tests/unit/test_edge_cases.py` | 26,337 B | 648 | `fdf62bdee7d5e2fc2150d3e67c0a74aab0a0e3c1` | Patches `simulation.*` globals of the deleted module; was ignore-globbed, never ran | `git show fdf62bdee7d5e2fc2150d3e67c0a74aab0a0e3c1 > /tmp/restore_edge_cases.py` |
| `tests/test_enhanced_demo.py` | 864 B | 31 | `907b471cff552e4d40a6b4a9c5fbb2f413fbce3f` | Toy numpy/pandas/altair smoke test, not project coverage; was ignore-globbed | `git show 907b471cff552e4d40a6b4a9c5fbb2f413fbce3f > /tmp/restore_enhanced_demo.py` |
| `tests/test_enhanced_gif.py` | 1,030 B | 40 | `ae474ffcb0e107be2ddb80c79a0f9d086d092356` | `Demo.gif` loader returning bool (not a pytest assertion); was ignore-globbed | `git show ae474ffcb0e107be2ddb80c79a0f9d086d092356 > /tmp/restore_enhanced_gif.py` |
| `tests/test_gif_loading.py` | 957 B | 39 | `617098596c77c711073a3037bc9fbce89924b21b` | Duplicate `Demo.gif` loader; was ignore-globbed | `git show 617098596c77c711073a3037bc9fbce89924b21b > /tmp/restore_gif_loading.py` |

General restore rule for any deleted file: `git log --diff-filter=D -- <path>` finds
the deleting commit; `git show <commit>^:<path>` recovers it. Blob hashes above
are the fastest path (`git show <blob> > <out>`).

## Class-level deletions (surgical, live code preserved verbatim)

Source blobs are pre-cleanup versions of the three files that were rewritten
in place (live classes kept byte-for-byte, only headers/imports trimmed):

| File (kept, rewritten) | Pre-cleanup blob | Removed classes | Kept classes |
|------------------------|------------------|-----------------|--------------|
| `tests/performance/test_performance.py` | `363349705fd175fdc6fe711467863d1b5b8d4b4e` | `TestVehicleDetectionPerformance` (~186 lines, darkflow `vehicle_detection_modern`), `TestSimulationPerformance` (~164 lines, darkflow `simulation` + pygame mocks), `TestPerformanceRegression` (~91 lines, darkflow) — all `@unittest.skip("Quarantined…")` | `TestSystemStress` (3 tests, verbatim) |
| `tests/security/test_security.py` | `dffeeabebdcd1d127d17922b1d2dbf85b3a95a24` | `TestInputValidation` (~200 lines, darkflow filenames/XSS/SQLi toys), `TestFileSystemSecurity` (~185 lines, traversal/permission toys), `TestAuthenticationSecurity` (~150 lines, placeholder password/session/RBAC never wired to the API) — first two skipped, auth skipped | `TestDataEncryption`, `TestLoggingSecurity` (verbatim; generic helpers only, see caveat in TESTING_DOCUMENTATION.md) |
| `tests/integration/test_integration.py` | `9d6ab9c6b0765fe622b2e75a47f73c761b9741f7` | `TestDetectionSimulationPipeline` (~100 lines, darkflow detect→sim), `TestDashboardIntegration` (~60 lines, legacy `app` module import) — both skipped | `TestMultiModuleCoordination`, `TestPerformanceIntegration`, `TestDataFormatCompatibility` (verbatim, incl. the honestly-skipped `test_03_error_message_formatting`) |

To view exactly what was cut: `git show 363349705fd175fdc6fe711467863d1b5b8d4b4e > /tmp/perf_before.py` (etc.)
then `diff /tmp/perf_before.py tests/performance/test_performance.py`.

## Supporting edits (not deletions)

| File | Change |
|------|--------|
| `tests/conftest.py` | `collect_ignore_glob` emptied (all six patterns pointed at files deleted above). Policy going forward: delete stale tests, don't quarantine them. |
| `tests/performance/test_performance.py` header/imports | Removed `os/shutil/sys/tempfile`, `Mock/patch`, top-level `psutil`, and the `sys.path.append(...Code/YOLO/darkflow)` shim. Live stress tests use local `psutil` imports with `skipTest` fallback. |
| `tests/security/test_security.py` header/imports | Removed `os/subprocess/sys`, `Mock/patch`, and both `sys.path.append(...darkflow)` shims. |
| `tests/integration/test_integration.py` header/imports | Removed `json/os/shutil/sys/tempfile`, `patch`, and both darkflow shims. Live classes need only `threading/time/unittest` (+ local `psutil`). |
| `docs/TESTING_DOCUMENTATION.md` | Rewritten to one honest page (pre-rewrite blob `7151494d0a15cf561bed26d17f373c55d86cab3b`). |
| `docs/TESTING_IMPLEMENTATION_COMPLETE.md` | Retired to a dated historical note (pre-retire blob `f7450a6784cde0c2d2c1b545f96c37cae338a95d`). |
| `docs/INDUSTRY_DEMO.md` §§ Pre-deployment/Demo script | Fixed non-existent commands (`adapters_onnx --source rtsp…`, `make bench-decide --registry… --count`) to the real `scripts/bench_detect.py` / `scripts/bench_decide.py` invocations. |

## What was deliberately NOT deleted

- `TestSystemStress`, `TestDataEncryption`, `TestLoggingSecurity`, and the
  `test_integration.py` coordination classes: live but weak (synthetic FFT/RNG,
  toy masking). Flagged as such in `TESTING_DOCUMENTATION.md`; replace with
  recorded-footage + API-boundary tests in Phase B rather than deleting blind.
- `evals/runner.py`, `scripts/bench_*.py`, `scripts/profile_device.py`: the real
  gates. Untouched.
