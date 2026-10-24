# Adaptive Traffic Signal Timer — narrated film

Evidence review: 14 October 2026. Narration: Microsoft Zira Desktop (synthetic voice).

## 01. A signal that responds — 00:00:00

Status: PROJECT OVERVIEW

Adaptive Traffic Signal Timer explores a practical question: can camera observations help traffic signals respond to actual demand? It combines an India-specific detector, queue estimation, configurable timing policies, and a simulator. This film explains the developed parts, data and models, results, development decisions, problems tackled, and the evidence still needed before real-world deployment.

Sources: README.md; docs/MASTER_PLAN.md

## 02. Why this problem matters — 00:00:23

Status: INDUSTRY OPPORTUNITY

Equal green times can waste service on empty approaches while another queue grows. Indian junctions add heterogeneous vehicles, irregular geometry, lane drift, encroachment, and monsoon conditions. The industry opportunity is a configurable system for investigating these conditions on ordinary edge hardware. Delay reductions are demonstrated in simulation; fuel, emissions, safety, and financial benefits still need measurement.

Sources: docs/MASTER_PLAN.md; src/adaptive_traffic/core/simulation/behavior.py

## 03. The developed parts — 00:00:48

Status: IMPLEMENTED; MATURITY VARIES

The repository contains detection backends, traffic types, queues, a topology-generic simulator, and signal policies. It also provides data converters, training notebooks, model registries, scorecards, tests, FastAPI routes, Streamlit views, monitoring, and deployment configuration. These parts have different maturity levels. Real model inference and offline replay coexist with mock API responses and unfinished field integration.

Sources: docs/ARCHITECTURE.md; src/adaptive_traffic/api/routes/detection.py

## 04. Architecture mapped with graphify — 00:01:16

Status: SOURCE-TRACED REVIEW

Graphify supplied the navigation map: seventeen hundred and fifty-six nodes and thirty-two hundred and sixteen relationships. Focused queries traced training, evaluation, queues, and actuation. The design separates domain types, ports, and adapters, keeping heavy detection dependencies behind backend seams. TrafficSimulation and CityProfile are central hubs. Graph relationships guided the review; current source and recorded evidence determined the claims.

Sources: graphify-out/graph.json; docs/ARCHITECTURE.md; src/adaptive_traffic/core/domain.py

## 05. From frame to timing plan — 00:01:44

Status: OFFLINE LOOP IMPLEMENTED

A frame passes through detection and queue estimation. The closed-loop bridge inserts estimated class mix into the simulator's demand state, refreshes the green plan, and translates it into an NTCIP cycle configuration. The same run-frame function supports the lab runner and integration tests. Recorded-image actuation uses a mock transport; a connected roadside controller has not been validated.

Sources: src/adaptive_traffic/core/closed_loop.py; scripts/run_closed_loop.py; tests/integration/test_closed_loop.py

## 06. Perception on real CCTV imagery — 00:02:07

Status: ACTUAL FP32 INFERENCE

The canonical detector is a YOLO version eight nano model exposed through ONNX Runtime. It recognises car, motorcycle, bus, truck, bicycle, and autorickshaw. This view uses an actual held-out TrafficCAM image and predictions from the selected FP32 registry. The scan animation is a presentation effect. Visible boxes do not establish complete recall or a live camera connection.

Sources: models/registry/india-yolov8n-final/metadata.json; src/adaptive_traffic/core/detection/adapters_onnx.py; data/trafficcam/images/val/

## 07. Estimating the waiting queue — 00:02:30

Status: CALIBRATION STILL REQUIRED

Queue estimation groups detections by lane and direction, uses camera geometry and vehicle lengths, and smooths estimates over time. Per-class counts feed timing policies. Camera width and height are now configurable, replacing a fixed-resolution assumption. Each installed camera still needs calibration. Counting every labelled vehicle in an image is not equivalent to measuring vehicles waiting in a defined queue zone.

Sources: src/adaptive_traffic/core/analytics/queue_estimator.py; src/adaptive_traffic/config/city_profile.py; tests/unit/test_estimator_geometry.py

## 08. Green time follows vehicle mix — 00:02:54

Status: CANONICAL POLICY PIPELINE

The active controller is a policy pipeline. Green demand equals startup time plus each count multiplied by its discharge headway. Default headways give a bike one second, a car or auto two, and a bus or truck three-point-two. City bounds and demand-share caps constrain the plan. Clockwise service is the default; maximum-demand order remains configurable.

Sources: src/adaptive_traffic/core/control/policies.py; src/adaptive_traffic/core/simulation/engine.py

## 09. One scheduler, several geometries — 00:03:16

Status: 3 / 4 / 5-WAY TEST COVERAGE

An early four-way-only engine could not represent irregular intersections. The replacement expresses approaches and compatible movements as configuration. Non-conflicting approaches can share service, and empty groups are skipped. Evaluation covers three, four, and five-way geometries using the same engine. This is a simulation capability; a physical junction's movement conflicts and clearance requirements still need engineering validation.

Sources: docs/MASTER_PLAN.md; src/adaptive_traffic/core/simulation/engine.py; configs/evals/scenarios.yaml

## 10. Operator and emergency priority — 00:03:41

Status: LAB POLICY; FIELD SAFETY UNPROVEN

An active manual protocol owns its covered route and suppresses emergency preemption there. Elsewhere, emergency priority can apply before normal adaptation. Tests cover this precedence. The manual registry and audit trail are in memory. Durable approvals, deployment-grade authorisation, and safe emergency transitions on actual controller hardware are not established by these lab tests.

Sources: src/adaptive_traffic/core/control/policies.py; src/adaptive_traffic/core/closed_loop.py; tests/unit/test_policies.py

## 11. Tune a city through data — 00:04:03

Status: CONFIGURATION IMPLEMENTED

City profiles collect lane counts, fleet mix, behaviour, weather, detector calibration, signal limits, and discharge headways. Mumbai, Delhi, Bangalore, and a tier-two default are provided. Profiles change behaviour without editing the engine. These are configurable presets, not evidence those cities operate this system. Real installations require measured geometry, local headways, and operational acceptance.

Sources: src/adaptive_traffic/config/city_profile.py; src/adaptive_traffic/config/city_profiles.py

## 12. A controlled world for hard cases — 00:04:28

Status: SYNTHETIC SIMULATION

The simulator combines three behaviour presets and four weather states. Lane drift, encroachment, and violation probabilities represent driver behaviour. Weather alters speed, capacity, and observed detection confidence. This enables repeatable stress tests and true-versus-observed queue comparisons. Weather is synthetic, not a connected meteorological feed. Incident scenarios are approximations; their results are not observed roadside events.

Sources: src/adaptive_traffic/core/simulation/behavior.py; src/adaptive_traffic/core/simulation/weather.py; evals/runner.py

## 13. Evaluation against fixed-time — 00:04:55

Status: 11-SCENARIO CANONICAL MATRIX

The canonical evaluation runs eleven scenarios in adaptive and fixed-time modes. It records waiting time, throughput, simulated queue error, and decision latency. Saved scorecards support comparisons and regression flags. A fifteen-scenario review snapshot also exists, but the current scenario configuration contains eleven. This film uses the latest stored eleven-scenario scorecard consistently and separates simulation outcomes from detector accuracy.

Sources: configs/evals/scenarios.yaml; evals/runner.py; evals/results/scorecard_1790842116.json; docs/REVIEW_BRIEF.md

## 14. All eleven reduce average wait — 00:05:21

Status: STORED SIMULATION RESULTS

In the selected scorecard, adaptive control reduces average wait in all eleven scenarios, by roughly nineteen to seventy-five percent. Clear five-way wait moves from fifty-four-point-two-eight seconds to fourteen-point-three-two. Heavy four-way monsoon moves from twenty-eight-point-three-two to twelve-point-six-seven. Throughput is lower in two scenarios. The achievement is lower average wait across this matrix, not universal improvement in every metric.

Sources: evals/results/scorecard_1790842116.json

## 15. Measure before optimising — 00:05:47

Status: RECORDED WORKSTATION BENCHMARKS

The simulator baseline reaches twenty-eight thousand five hundred and three steps per second, fifty-seven times its target. The later estimate-plus-decision benchmark is two-point-nine-three milliseconds at the ninety-fifth percentile for three hundred detections, below a ten-millisecond budget. Real-frame FP32 inference is five-point-one to eight-point-two frames per second on the development CPU. These separate measurements are not an end-to-end field guarantee.

Sources: docs/BENCHMARKS.md

## 16. What data was actually used — 00:06:11

Status: PROVENANCE BY PURPOSE

IITM HeTra supported an early pilot. BMD forty-five supplied canonical training and official validation. A local TrafficCAM subset enabled real-CCTV tests and a fine-tune candidate. Synthetic images supported software fixtures but failed as photographic detector quality evidence. ITD-X teacher predictions form a separate pseudo-label pool, not human ground truth. IDD is a future evaluation source, not a completed local test.

Sources: docs/BENCHMARKS.md; docs/DATASET_SPEC.md; notebooks/training_output_zips/itd_x_2026-09-22.zip

## 17. One contract, stable class IDs — 00:06:39

Status: CONVERTERS IMPLEMENTED

Sources normalise into JPEG images, YOLO text labels, a dataset configuration, calibration frames, and capture metadata. Converters accept YOLO, COCO, Pascal VOC, and TrafficCAM annotations. Fine-grained passenger and goods categories merge into six stable classes; unsupported categories are excluded. Source splits are preserved where available. TrafficCAM keeps whole videos together, preventing adjacent-frame leakage across training and validation.

Sources: scripts/prepare_dataset.py; docs/DATASET_SPEC.md; tests/unit/test_prepare_dataset.py

## 18. BMD-45: scale without disk failure — 00:07:07

Status: CANONICAL DATA WORKFLOW

The official IISc BMD dataset card lists thirty-five thousand seven hundred and ninety-two training images and ten thousand one hundred and ninety-four validation images. Large PNG storage exceeded convenient Colab limits. Folder-wise processing, JPEG conversion, and Drive-native resume-safe preparation addressed that constraint. The repository reports results on the official validation pool, described as full ten-k validation.

Sources: https://huggingface.co/datasets/iisc-aim/BMD-45; notebooks/train_bmd_loop.ipynb; notebooks/train_bmd_finale_drive.ipynb

## 19. Eight cumulative training loops — 00:07:33

Status: TRAINING CHAIN COMPLETED

The chain processes eight training folders cumulatively. Loop one starts from COCO weights for twenty epochs; later loops use the previous best checkpoint for twelve. Rehearsal samples from earlier folders preserve previous learning, and a fixed validation anchor guides continuation. Recorded overall mean average precision rises from point-seven-nine-four-nine to point-eight-two-nine-three, with no forgetting reported across the anchored checks.

Sources: notebooks/train_bmd_loop.ipynb; docs/BENCHMARKS.md

## 20. The finale and its packaged model — 00:07:57

Status: CANONICAL CHECKPOINT TRAINED

The finale jointly polishes the loop-eight best checkpoint for five epochs, with a learning-rate setting of point-zero-zero-two. The archived CSV records point-eight-four-seven-seven mean average precision on the full official validation pool. Loop eight used one validation folder, so these scores are not a paired same-split comparison. The roughly three-million-parameter model is packaged as ONNX; FP32 remains selected.

Sources: notebooks/train_bmd_finale_drive.ipynb; notebooks/training_output_zips/bmd_finale_2026-09-13.zip; models/registry/india-yolov8n-final/metadata.json; configs/device.yaml

## 21. Six classes, six measured results — 00:08:20

Status: FINALE BMD VALIDATION

The finale reports per-class results: car point-nine-one-eight-nine, auto point-nine-one-seven-one, motorcycle point-eight-eight-eight-seven, bus point-eight-four-six, truck point-eight-two-nine-four, and bicycle point-six-eight-five-nine. Bicycle remains the weakest class despite improvement over loop one. Mean average precision at point-five is a detector metric, not the percentage of all road vehicles correctly counted or a guarantee for another camera domain.

Sources: models/registry/india-yolov8n-final/metadata.json; docs/BENCHMARKS.md

## 22. Model history: compare like with like — 00:08:44

Status: DATASET-SPECIFIC RESULTS

The earlier HeTra pilot achieved point-nine-eight-one-six, but validation covered only car, bus, and auto. Its score is not directly comparable with six-class BMD validation. The model history represents improved coverage and stronger evidence, not a ranking by raw score alone. Fixed, Webster, fuzzy, and DQN controller classes exist as dormant alternatives; the evaluated runtime uses the policy pipeline.

Sources: docs/BENCHMARKS.md; models/registry/india-yolov8n/metadata.json; src/adaptive_traffic/core/control/controllers.py

## 23. TrafficCAM exposed the domain gap — 00:09:09

Status: CANDIDATE NOT PROMOTED

TrafficCAM exposed weaker cross-domain performance. On the same one hundred and eighty validation frames, the finale scored point-four-eight-eight and the fine-tuned candidate point-six-three-five, about thirty percent relative improvement. Yet a small fixed-threshold F1 sample tied, the BMD retention anchor remained unestablished, and candidate dynamic INT8 was slow. It remains local-only. The recorded run used twenty epochs despite an earlier ten-epoch notebook setting.

Sources: docs/BENCHMARKS.md; notebooks/train_trafficcam_loop.ipynb; notebooks/training_output_zips/trafficcam_candidate_2026-09-21.zip

## 24. The first INT8 failure changed the plan — 00:09:36

Status: QUALITY CLAIMS WITHDRAWN

The original static INT8 export looked plausible by size and speed, but real-image testing revealed all-zero detection scores. This was quantisation failure, not merely poor generalisation. Earlier INT8 quality claims were withdrawn; latency measurements alone were retained. The default switched to FP32, and packaging gained a non-zero-score guard. A smaller or faster artifact needs a quality test before promotion.

Sources: docs/BENCHMARKS.md; configs/device.yaml; notebooks/train_bmd_finale_drive.ipynb

## 25. Repaired INT8 still missed the gate — 00:10:02

Status: 11 OCTOBER 2026: KEEP FP32

Version-six-b quantises the backbone while keeping the final score and box tail in FP32. On official BMD validation, FP32 reproduced point-eight-four-six-nine; INT8 reached point-eight-two-two-four and nine-point-three-nine frames per second on the Colab CPU. Speed passed, but quality loss exceeded the allowed point-zero-two. TrafficCAM showed a similar loss. The decision was to keep FP32 and leave this candidate unpromoted.

Sources: evals/results/anchor_bmdval_2026-10-11.txt; docs/BENCHMARKS.md; scripts/requant_int8_v2.py; configs/device.yaml

## 26. Real pixels found contract bugs — 00:10:28

Status: FIXES COVERED BY TESTS

Real-footage checks found a bounding-box mismatch: ONNX emitted position and size while downstream code expected two corners. Correcting the contract reduced zero-queue frames from one hundred and forty-five out of one hundred and eighty to fifteen. A regression test locks the convention. The ignored NMS threshold was also connected, and configurable geometry replaced a fixed resolution. Better plumbing still needs real queue truth.

Sources: docs/BENCHMARKS.md; src/adaptive_traffic/core/detection/adapters_onnx.py; tests/unit/test_onnx_adapter.py; tests/unit/test_estimator_geometry.py

## 27. An evidence-led development loop — 00:10:53

Status: IMPLEMENTED WORKFLOW

Development combines loop engineering and graph engineering: measure, isolate the problem, make the smallest responsible change, verify, and record. Three redundant test orchestrators were removed in favour of Makefile gates. Ports and adapters limit hardware coupling; graphify makes relationships visible. Performance evidence avoided unnecessary engine rewrites. Notebooks, scorecards, metadata, and training archives preserve the reasons behind decisions.

Sources: docs/MASTER_PLAN.md; Makefile; docs/TRACK_RECORD.md; AGENTS.md

## 28. Scheduling learned from failed ideas — 00:11:20

Status: MEASURED DESIGN ITERATIONS

Naive proportional service favoured paired movements and starved a singleton. Discharge-following greens helped, but short phases wasted time on transitions. A fifteen-second efficiency floor improved the three-way result. Later, clockwise order met the operator's predictability requirement but caused four regressions against maximum-demand order. Those tradeoffs were documented while all eleven cases still beat fixed-time on average wait.

Sources: docs/BENCHMARKS.md; src/adaptive_traffic/core/control/policies.py; src/adaptive_traffic/core/simulation/engine.py

## 29. Controller wire tests caught defects — 00:11:44

Status: LOOPBACK PROOF; HARDWARE PENDING

Wire tests found incorrect BER object-identifier continuation bits and a one-byte length field that failed on large timing messages. Both were corrected. By October eleventh, GET response parsing was also implemented and covered by loopback tests, superseding an older stub description. This is useful protocol evidence, but interoperability with an actual traffic controller remains unvalidated.

Sources: src/adaptive_traffic/adapters/ntcip_stmp.py; tests/integration/test_stmp_wire.py; docs/MASTER_PLAN.md; docs/BENCHMARKS.md

## 30. Freshness, monitoring and device tiers — 00:12:07

Status: PRIMITIVES IMPLEMENTED

Slow perception can produce stale control inputs. The pipeline provides a bounded drop-oldest buffer and per-stage timing, with Prometheus histograms for detection, estimation, decision, and actuation. Device configuration selects ONNX for lower tiers. TensorRT FP16 and engine caching are implemented with ONNX fallback, but Jetson latency is not measured. These primitives still need a connected live capture runner.

Sources: src/adaptive_traffic/core/pipeline.py; src/adaptive_traffic/core/monitoring.py; src/adaptive_traffic/core/detection/adapters_tensorrt.py; configs/device.yaml

## 31. Interfaces are built; wiring varies — 00:12:32

Status: DEMO AND SERVICE SCAFFOLD

FastAPI supplies detection, signals, analytics, health, and metrics routes. Streamlit supplies dashboard and demonstration views. Offline replay executes the real detector-to-plan loop with mock actuation. The image-upload endpoint still returns canned detections, and several stores are in memory. Docker and monitoring configuration exist, but their presence does not establish an operated production service or persistent infrastructure.

Sources: src/adaptive_traffic/api/routes/detection.py; src/adaptive_traffic/api/routes/health.py; src/adaptive_traffic/ui/replay.py; configs/docker/

## 32. Analytics and V2X: accurate status — 00:12:58

Status: PARTIAL IMPLEMENTATIONS

Forecasting uses a simplified seasonal-plus-trend method; no field forecasting benchmark is established. V2X interfaces represent Basic Safety Messages and signal phase-and-timing messages, with UDP and fusion scaffolding. Their encoder and decoder explicitly use simplified payloads rather than a complete ASN-point-one UPER codec. Connected-vehicle standards interoperability is unfinished. Multi-junction learned coordination is an extension slot, not a trained deployed agent.

Sources: src/adaptive_traffic/core/analytics/forecaster.py; src/adaptive_traffic/adapters/j2735.py; src/adaptive_traffic/core/control/policies.py

## 33. What the project has achieved — 00:13:26

Status: EVIDENCE-SCOPED ACHIEVEMENTS

Achievements include a completed BMD training chain and finale, six-class validation, reproducible packaging, configurable queues and policies, topology-generic simulation, and lower average wait across the canonical matrix. Real-footage replay and loopback tests connect the components. Testing also exposed a dead quantised model, a box-contract mismatch, and malformed controller messages. Documenting and correcting these defects is part of the engineering achievement.

Sources: docs/MASTER_PLAN.md; docs/BENCHMARKS.md; models/registry/india-yolov8n-final/metadata.json; evals/results/scorecard_1790842116.json

## 34. What remains before a field pilot — 00:13:53

Status: NOT COMPLETED

The next proof is live capture, camera-calibrated queue truth, and a shadow-mode field pilot. Controller compatibility, clearance behaviour, emergency safety, and target-device performance need validation. API inference wiring, durable operational state, and standards-grade V2X remain incomplete. Pedestrian phases, live weather, multi-junction coordination, and an approved INT8 model are not delivered. Fresh pytest passes one hundred and nine tests with one skip; the canonical lint gate is not clean.

Sources: docs/MASTER_PLAN.md; src/adaptive_traffic/api/routes/detection.py; src/adaptive_traffic/adapters/j2735.py; artifacts/project-film/qa/flake8.txt

## 35. Why industry should pay attention — 00:14:23

Status: PILOT CASE; NOT FIELD ROI

Industry attention is justified by local traffic taxonomy, configurable policies, modest model size, modular backends, and an auditable evidence trail. A signal vendor or city partner can help convert simulation promise into verified operation. The next collaboration supplies representative footage, hand-counted queues, controller access, and target edge devices. Savings, emissions reductions, safety improvements, and return on investment must be measured in that pilot.

Sources: docs/MASTER_PLAN.md; docs/ARCHITECTURE.md; docs/BENCHMARKS.md

## 36. A disciplined path to the road — 00:14:50

Status: PROPOSED NEXT STEPS

A responsible sequence is calibrated offline replay, live shadow-mode comparison, then controller-bench and safety review before a limited supervised pilot. Report both delay and throughput, queue error, missed detections, latency, failures, and recovery. Data and model rights need provenance review: the ITD-X pseudo pool is marked research-only in its archive and remains separate from the canonical BMD model.

Sources: docs/DATASET_SPEC.md; notebooks/training_output_zips/itd_x_2026-09-22.zip; docs/MASTER_PLAN.md

## 37. A prototype built to earn trust — 00:15:13

Status: REVIEWED 14 OCTOBER 2026

Adaptive Traffic Signal Timer has moved from a generic four-way concept to a modular, India-focused engineering prototype. Its strongest story combines model learning, measured policy improvements, and problems discovered through realistic testing. The next milestone is independently verified field proof. This film separates implemented code, recorded results, experimental candidates, and proposed work, presenting achievements confidently without overstating completion.

Sources: README.md; docs/MASTER_PLAN.md; docs/BENCHMARKS.md; artifacts/project-film/EVIDENCE.md
