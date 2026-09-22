# Colab Workflow — GPU Notebooks and Hand-Back Zips

> The only GPU steps in this project live in Colab (Free T4). Everything else
> runs on CPU. This page is the contract between notebook runs and the repo.

## Notebook index (`notebooks/`)

| Notebook | Runtime | Purpose | Hand-back |
|---|---|---|---|
| `train_bmd_loop.ipynb` | T4 | 8-loop cumulative BMD-45 chain (canonical training) | loop zips |
| `train_bmd_finale_drive.ipynb` | T4 | 5-epoch joint polish from loop-8 best | finale zip |
| `eval_trafficcam_drive.ipynb` | CPU (T4 optional) | TrafficCAM download → convert → mAP + benches | `trafficcam_eval_<date>.zip` |
| `train_trafficcam_loop.ipynb` | T4 | TrafficCAM fine-tune → registry candidate | `trafficcam_candidate_<date>.zip` |
| `pseudo_itd_x.ipynb` | T4 | ITD-X compare + pseudo-labels | `itd_x_<date>.zip` |

## Hand-back convention

- Zips go in `notebooks/training_output_zips/` — **gitignored, local-only, never committed**.
- Every zip carries metrics + per-frame rows + the exact inputs to reproduce it.
- On receipt: validate contents → run promotion gates → record verdict in
  `docs/BENCHMARKS.md`. Promotion requires: target metric up **and**
  BMD-Val within −0.02 (no forgetting) **and** int8 ≥4.5fps if quantized.
  Anything less is staged (local-only registry), never promoted.

## Hard-won rules (paid for in real debugging sessions)

1. **Cells are cwd-proof.** Every Colab `!` line runs in a fresh shell rooted
   at `/content` — never rely on `cd` persisting. Absolute paths everywhere.
2. **Fail fast with asserts**, not traceback archaeology: data.yaml exists,
   frame counts, label-distribution permutation checks live in the cells.
3. **Pin the branch.** Notebooks `git clone --branch <working-branch>` and
   replace foreign checkouts; the setup cell prints `repo: <branch> <SHA>`.
   Paste that SHA with any bug report. (Remove the pin once the work merges
   to `main`.)
4. **Static quantization is guilty until proven innocent.** Every export cell
   asserts non-zero max scores on a calibration frame before packaging, with
   dynamic fallback. A silent int8 killed a full benchmark cycle once.
5. **Taxonomy alignment is verified, not assumed.** Cross-model evals remap
   label ids AND assert the remapped distribution is a permutation of source.
   Ultralytics resolves symlinks — eval trees use copies, never links.
6. **Pseudo-labels are model-derived GT**: `SOURCE.txt` provenance in-zip,
   12-frame overlay spot-check before trust, reported separately from human GT.
