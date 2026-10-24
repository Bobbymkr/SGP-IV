# Adaptive Traffic Signal Timer — film evidence

Reviewed on **14 October 2026** against the existing working tree. The film is a project explanation, not a production certification. Existing uncommitted work was retained.

The knowledge graph supplied navigation; source, current configuration and primary recorded artifacts supplied the claims. Graphify reported **1,756 nodes and 3,216 links**, with 141 distinct source-file entries. Query vocabulary: architecture, pipeline, dataset, training, model, benchmarks, evaluation, quantization, actuation, achievements, findings, readiness. Focused `query`, `explain QueueEstimator`, `explain J2735Adapter`, and the full-ID `path` from `run_frame` to the real STMP adapter were used. Some graph edges are inferred; the illustrated architecture is a conceptual view, not a reproduction of every graph edge.

## Evidence hierarchy

1. Current executable source and selected configuration establish implementation and default selection.
2. Archived training CSVs, model metadata and evaluation logs establish recorded results.
3. Current benchmark notes and the master-plan change log establish chronology and corrections.
4. Older demo material is used only after checking later corrections. Its unqualified production claims are not repeated.

## Claims used in the film

| Subject | Evidence | Meaning and limits |
|---|---|---|
| Canonical model | [Registry metadata](../../models/registry/india-yolov8n-final/metadata.json), [device config](../../configs/device.yaml) | YOLOv8n six-class model, 640 input; `prefer_int8: false`. Metadata still says quantization INT8; it is not the authority for which artifact is selected today. |
| Finale result | `notebooks/training_output_zips/bmd_finale_2026-09-13.zip`, internal `results.csv`, epoch 5 | mAP50 **0.84767**, rounded **0.8477**; mAP50–95 **0.69058**. These are original training validation results, not new retraining performed for this film. |
| Class results | [Registry metadata](../../models/registry/india-yolov8n-final/metadata.json) | Car .9189, auto .9171, motorcycle .8887, bus .8460, truck .8294, bicycle .6859. |
| Model sizes | Local file sizes | FP32 12,269,662 bytes = 12.27 decimal MB / 11.70 MiB. Original INT8 3,389,614 bytes = 3.39 MB / 3.23 MiB. File presence does not establish INT8 quality. |
| Cumulative chain | [Notebook](../../notebooks/train_bmd_loop.ipynb), [benchmarks](../../docs/BENCHMARKS.md) | Eight loops .7949 → .8293, with rehearsal and anchored checks. The chain's fixed anchor and the finale's full validation must not be assumed to be identical subsets. |
| Dataset definition | [Official IISc BMD-45 card](https://huggingface.co/datasets/iisc-aim/BMD-45) | Current primary card lists 35,792 train / 10,194 val, COCO labels, 14 categories. Repository calls the validation pool “full 10k”. Those are approximate shorthand, not a claim of exactly 10,000 processed images. |
| Six-class mapping | [Converter implementation](../../scripts/prepare_dataset.py) | `MERGE_B` folds car variants into car, several passenger carriers into bus and LCV into truck; Other excluded. Older dataset prose calling merged classes “dropped” is inaccurate. Source names are not six independent datasets. |
| Split hygiene | [Dataset contract](../../docs/DATASET_SPEC.md), [converter](../../scripts/prepare_dataset.py) | Source splits respected where provided; TrafficCAM hashes whole videos. Junction/day checking is conditional on capture metadata, not proved for every source. |
| HeTra pilot | [Benchmark pilot row](../../docs/BENCHMARKS.md) | .9816 on only car/bus/auto validation coverage. Not comparable as a superior six-class generalisation result. |
| TrafficCAM subset | Local counts and [benchmark notes](../../docs/BENCHMARKS.md) | 2,340 converted frames: train 1,860 / val 180 / test 300; documented 78 videos. This is the local subset, not the complete external dataset. |
| TrafficCAM candidate | [Benchmark head-to-head section](../../docs/BENCHMARKS.md) and candidate zip | Finale .488 versus candidate .635 on 180 val frames. Candidate score is recorded from the training log; .635 was not recomputed for this film. F1 tie belongs to a separate 50-frame fixed-threshold check. Candidate remains local-only; retained-BMD gate unresolved. Recorded run 20 epochs, earlier setting 10. |
| Original INT8 failure | [Detector QA corrections](../../docs/BENCHMARKS.md), [selected config](../../configs/device.yaml) | Original all-zero score artifact invalidates its quality claims. Historical latency rows survive but do not prove detector utility. |
| Repaired static INT8 | [Full-val anchor](../../evals/results/anchor_bmdval_2026-10-11.txt), [benchmarks](../../docs/BENCHMARKS.md) | FP32 .8469 / INT8 v6b .8224, loss .0245 > .02 allowed. Colab CPU 6.58 / 9.39 fps. Speed passes, quality fails. Still KEEP FP32. TrafficCAM .4882 / .4646 corroborates the loss. |
| Queue-box fix | [ONNX source](../../src/adaptive_traffic/core/detection/adapters_onnx.py), [test](../../tests/unit/test_onnx_adapter.py), [benchmarks](../../docs/BENCHMARKS.md) | XYWH versus XYXY mismatch corrected; historical zero queues 145/180 → 15/180. Demonstrates contract improvement, not calibrated physical queue accuracy. |
| Queue quality gap | [Queue proxy caveats](../../docs/BENCHMARKS.md), [estimator](../../src/adaptive_traffic/core/analytics/queue_estimator.py) | Historical real-image queue proxy RMSE ~28.89 counts all visible labels versus queue-zone estimates; it is not a matching-definition field queue score. Geometry is now configurable; installed cameras still need calibration and hand-count GT. |
| Adaptive outcomes | [Chosen scorecard](../../evals/results/scorecard_1790842116.json) | Latest stored eleven-scenario scorecard: 11/11 lower average wait, **19.26–75.25%**. Adaptive throughput lower in clear 3-way (720 vs 780 vph) and aggressive waterlogged 4-way (396 vs 480 vph). Film does not claim universal throughput gains. |
| Fifteen-scenario snapshot | [Review brief](../../docs/REVIEW_BRIEF.md), `scorecard_1790419766.json` | A separate stored review snapshot, not the currently configured eleven-scenario gate. Surat-related review claims do not establish a current deployed city profile. |
| Performance | [Benchmarks](../../docs/BENCHMARKS.md) | 28,503 sim steps/s: historical workstation baseline. 2.93 ms p95 at 300 boxes: latest documented estimate+state+decide row, excludes detection/transport. 5.1–8.2 fps FP32: historical real-frame CPU inference. No new benchmark or field SLA inferred. |
| Policies | [Policy source](../../src/adaptive_traffic/core/control/policies.py), [closed loop](../../src/adaptive_traffic/core/closed_loop.py) | Weighted discharge, clockwise/argmax, demand-share cap, manual/emergency precedence. Legacy DQN/fuzzy/Webster are dormant. Manual storage is in memory; durable approvals and field-safe emergency clearance not validated. |
| STMP fixes | [Adapter](../../src/adaptive_traffic/adapters/ntcip_stmp.py), [wire tests](../../tests/integration/test_stmp_wire.py), [change log](../../docs/MASTER_PLAN.md) | Corrected BER continuation/lengths and implemented GET parser by Oct 11. Older benchmark “parser stub” statement superseded by current code. Loopback tests are not physical controller interoperability. |
| V2X | [J2735 source](../../src/adaptive_traffic/adapters/j2735.py) | BSM/SPAT interfaces and simplified codec. No complete ASN.1 UPER interoperability or connected-vehicle certification claimed. |
| API and UI | [Detection route](../../src/adaptive_traffic/api/routes/detection.py), [replay](../../src/adaptive_traffic/ui/replay.py) | Detection upload route canned; offline replay real detector, mock STMP. Single camera's direction split is illustrative. No live RTSP caller. |
| Monitoring / tiers | [Pipeline](../../src/adaptive_traffic/core/pipeline.py), [TRT adapter](../../src/adaptive_traffic/core/detection/adapters_tensorrt.py), [device config](../../configs/device.yaml) | Buffer and histograms implemented; TRT code/mock tests/fallback present. No Jetson speed or mixed-hardware universal validation claimed. |
| Pseudo-label provenance | `itd_x_2026-09-22.zip`, internal `pseudo_itd_x/SOURCE.txt` | Teacher-derived, NOT human ground truth; archive says IIT Roorkee ITD-X CC-BY-NC/research-only. Rights status is reported from repository provenance, not a legal conclusion. This pool is separate from BMD canonical training. |
| Current verification | [pytest log](qa/pytest.txt), [lint log](qa/flake8.txt) | **109 passed, 1 skipped** in 59.23s after executing outside the restrictive sandbox. Canonical flake8 command reports **494 formatting findings: 488 E501, 6 E203**. This does not constitute a green `make verify` gate. pyproject's flake8 options are not honoured by the current plain flake8 invocation. No unrelated application code was repaired for this film. |

## Asset provenance and presentation choices

- Actual demonstration image and predictions: [detections.json](assets/detections.json); held-out TrafficCAM val image, canonical FP32 inference at confidence .45. Six predictions were produced. This is an illustration, not a benchmark rerun or recall proof.
- The traffic motions, graph layout, buffer flow and pipeline diagrams are authored schematics. Moving scan line is an editorial overlay.
- Charts are authored with matplotlib from the cited project values. Original standalone charts are in `assets/`.
- Narration is locally generated with the installed Microsoft Zira Desktop voice; it does not impersonate a project member. Narration pace is rate 2.
- No stock footage, invented field testimonials, city deployment claims, measured ROI, or external industry endorsements are used.
- BMD factual counts above are attributed to the current [official dataset card](https://huggingface.co/datasets/iisc-aim/BMD-45). Project work remains distinct from the upstream authors' dataset and annotation pipeline.

## What is proposed, not delivered

Live capture and recovery; site-calibrated hand-count queue validation; shadow-mode field study; actual controller compatibility and clearance validation; emergency safety validation; on-device Jetson results; production inference wiring and durable state; complete V2X UPER; pedestrian phases; live weather source; multi-junction learned coordination; INT8 promotion; verified field ROI.

Older documents contain stale line numbers and stronger readiness language. The film deliberately uses later corrections and current implementation rather than repeating those statements.

## Problems and responses across the development record

| Problem identified | Evidence that exposed it | Response to date | Remaining limit |
|---|---|---|---|
| Hardcoded four-way phases | Initial architecture review | Configurable approach sets and compatibility groups | Field movement-conflict validation |
| Autorickshaw absent from domain taxonomy | India vehicle-mix review | AUTO added; stable six-class contract | Additional fine-grained classes are merged, not independently evaluated |
| Hardware-bound detection dependencies | Dependency review and heavy module imports | Detector port; adapter-confined lazy heavy imports | Whole-repo architecture is a design rule, not a claimed completed independent audit |
| Redundant/obsolete test runners and missing baseline | Initial test/performance review | Legacy runners deleted; Makefile gates; baseline measured | Canonical lint invocation still disagrees with formatting settings |
| Simulator considered slow without measurement | 28,503 steps/s baseline | Avoided unnecessary Rust/Numba rewrite | Optimise only if a later measured bottleneck warrants it |
| Unavailable authority images | Training access constraints | HeTra pilot, then official BMD source; external teacher pseudo pool kept separate | Authority/live installation feed absent |
| VOC image paths, split files and BOM | Converter dry runs and source layout | Recursive image indexing, BOM-tolerant membership, absolute dataset paths, val/test fallback | Metadata-dependent split checks cannot prove absent metadata |
| Colab disk pressure from large PNG data | Dataset size and preparation trials | Folder-wise conversion to JPG q92; cumulative rehearsal; Drive-native resume-safe prep | Drive reliability and operational training resources still external |
| Inconsistent schemas / source spellings | BMD/TrafficCAM annotation census | Stable mapping; aliases; polygon/RLE/bbox support; test coverage | Pedestrians intentionally not a detector class |
| Training forgetting risk | Fixed anchor checks after each loop | Rehearsal plus low-LR finale | Candidate cross-domain fine-tune has not passed BMD retention gate |
| Static quantisation export failure | Frame-reader init bug and later all-zero real-image scores | Init correction, FP32 fallback, non-degeneracy guard, later partial-backbone v6b | Alive v6b still exceeds allowed mAP50 loss |
| Synthetic fixture images unsuitable for detector evaluation | Working FP32 still predicts no vehicles on 576 schematics | Real TrafficCAM held-out imagery adopted | Need installation-specific recorded footage |
| ONNX tensor layout mismatch | First real export/adapter bring-up | Transpose export layout where needed | Different export variants still need contract checks |
| Bounding-box shape mismatch | Real frames silently became zero queues | XYXY output plus regression test | NMS and class-wise recall still merit separate evaluation |
| NMS setting ignored | Source review and threshold comparison | Constructor threshold wired; default retained because measured F1 neutral | Small-object recall, not the tested NMS changes, remains a likely lever |
| Queue proxy mismatch / resolution assumption | Large undercount and mismatched image dimensions | Configurable frame geometry; explicit GT-definition caveat | Camera calibration and queue-zone hand counts required |
| Naive proportional service starved singleton | Three-way simulation iteration | Discharge following, efficiency floor, starvation-bounded argmax option | Current clockwise choice carries accepted order costs |
| Tiny greens increased transition losses | Four-way regression during timing iteration | 15-second efficiency floor | Local saturation headways and clearance requirements need calibration |
| Clockwise predictability increased waits versus argmax | Four regressions in policy comparison | Documented operator tradeoff; argmax selectable | Operator acceptance and field comparison |
| Slow inference can accumulate old frames | Pipeline architecture review | Bounded drop-oldest buffer; stage instrumentation | No live capture/recovery integration |
| Staged benchmark counted frames it dropped | Implausible timing during initial stages flag | Inline process path for per-frame accounting | Bench input choice remains explicit; noise tests only prove latency |
| Controller OIDs and large packets malformed | Wire tests | BER continuation and long-length fixes | Physical controller response/compatibility |
| GET parser was a stub | Protocol coverage review | Parser and loopback tests implemented Oct 11 | Fail-closed defaults must not be confused with verified hardware values |
| TrafficCAM fine-tune improved mAP but did not satisfy promotion | 180-frame mAP, separate 50-frame F1, slow dynamic INT8 | Local-only alternative; canonical unchanged | Retained-BMD score, robust queue utility, acceptable target-device speed |
| Optimizer silently overrode requested fine-tune settings | Recorded TrafficCAM run log | Actual AdamW/20-epoch provenance documented | Do not equate requested LR with executed optimizer settings |
| Phantom readiness claims | Current health route/tests and source review | Registry/tier readiness; documentary claims narrowed | API remains partly mock; deployment operations unproven |
| V2X transport confused with standards implementation | Source comments in encoder/decoder | Film explicitly labels simplified payload scaffolding | Full codec and interoperability |

The film focuses on the material engineering problems above. Minor implementation details and historical parameter edits are retained here so the presentation can be reviewed without treating a summary as an exhaustive audit of every line of code.

Graph refresh after the review: `graphify update .` rebuilt **1,763 nodes / 3,324 edges / 131 communities** and preserved a backup of the earlier curated graph. The film's 1,756/3,216 count describes the graph used at the start of the review. Generated film artifacts are excluded through `.graphifyignore`. The tool noted changed community labels and several unsupported/no-symbol files; queries were cross-checked against source. The installed skill reports a newer version than the CLI package, so no claim of latest-version tool coverage is made.

Final query vocabulary check corrected the absent term problems to exact graph tokens bug / findings / readiness; the focused corrected query was run. The finale comparison was also refined after checking VAL_FOLDERS = [images_000] in the loop notebook: L1–L8 use one official-val folder, finale uses the full pool. The final video therefore does not present .8477 minus .8293 as a controlled same-split gain.



Final artifact verification: full audio/video decode passed; 1920x1080, 24 fps, H.264/AAC, 37 chapters, visible captions plus a selectable English track, motion verified in seven encoded scenes. Duration 939.604667s; 28559851 bytes. SHA-256: 23c197b280916a1d16f93873ad235a3f2d77182e922d8e845f74a0ddc80f9ab1
