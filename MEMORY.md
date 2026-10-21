# Shared memory — all harnesses read this (OpenCode, Codex, Omnirush, ChatGPT-cloud)

Single local brain. No daemon, no cloud, no embeddings. Episodic facts live in
`sqlite-memory-mcp` (FTS5). Code structure lives in `codebase-memory-mcp` (BM25-only).
This file is the flat entry point — no `@`-imports (only Claude resolves those).

## Rules for every harness

1. Read this file + `docs/agent-memory/claims/board.md` at turn start (pull, never full dump).
2. Search before writing: `memory_search` / `failure_search` first, then write.
3. Scope keys per project: `scope="project"`. Global scope is banned (cross-project bleed).
4. On finish: `memory_write` 1-3 durable facts + `failure_record` on any dead end.
5. Conflicts: same machine, file locks via `claims/board.md` (advisory). SQLite WAL handles the rest. Git backup.

## Where things live

- Episodic: `sqlite-memory-mcp` → DB `~/.claude/claude.db` (WAL+FTS5, 23 tools, 0 external deps).
  Pull pattern: `memory_search query="<topic>"` → `memory_read` only on hit.
- Structural: `codebase-memory-mcp` CLI/MCP, repo-only, BM25-only, no watcher global.
  `npx -y codebase-memory-mcp cli search_graph '{"name_pattern":".*Foo.*","label":"Function"}'`
- Handoffs: `docs/agent-memory/handoffs/active/` → move to `archive/` when done.
- Topics: `docs/agent-memory/topics/<slug>.md` (1 page max each).

## Project facts (seed)

- Stack: YOLOv8n → ONNX opset17 fp32 (`models/registry/india-yolov8n-final/`), int8 voided 2026-09-21.
- Gates: `make loop-fast` <30s, `make verify` 122 passed/1 skipped, `make eval` 11/11.
- UI: Streamlit dashboard = 6 pages / 9 tabs in `src/adaptive_traffic/ui/` (views/, not pages/).
  Every number tagged MEASURED / ILLUSTRATION / SPEC. Measured facts from `ui/_facts.py`,
  money+units from `ui/_india.py` (per-city fuel, USD/INR 94.77, carbon ₹8,150/t IISD).
  No dollars, no gallons in the UI. Run: `.venv\Scripts\python.exe -m streamlit run src/adaptive_traffic/ui/app.py --server.port 8503`.
- Watcher ignores: `.venv/ __pycache__/ data/ models/ checkpoints/ colab_outputs/ notebooks/training_output_zips/ graphify-out/ vault/ *.pt *.onnx *.db`
