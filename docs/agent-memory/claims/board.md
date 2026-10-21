# Claims board — advisory locks, single machine

One row per active work item. Check before starting shared work.

| resource | owner | since | ttl_min | note |
|----------|-------|-------|---------|------|
| _example | - | - | 30 | delete this row when real claims exist |

Rules: owner = `<harness>/<session>` (e.g. `opencode/a1b2`). Expired rows are free.
Handoff = move row, never duplicate. Git commit board with handoffs.
