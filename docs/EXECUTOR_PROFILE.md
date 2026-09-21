# Who I Am as an Executor - Proof From This Project Only

## How to read this document

This document uses only proof from this repo and from your one request for this document.
No guess. No outside story.

Every point has one of three marks:

- Proved: we have a file, line, number, or commit for it.
- Likely: we see a pattern, but proof is not full.
- Unknown: we do not have proof, so we do not say.

Language is simple on purpose. Hard words are explained in short words.

## Short summary - you in 10 lines

1. You pick real problems, not toy problems.
2. You build for India roads, not for a demo screen.
3. You measure first, then you change.
4. You make one clear way to check work.
5. You work in small done steps.
6. You keep code clean with clear walls between parts.
7. You write down weak points in the open.
8. You say no to extra work when numbers say no.
9. You use free and cheap tools in a smart way.
10. You finish and you keep proof of the finish.

## 1. Why you chose this project

Proved.

You chose traffic signals because it is a real pain. Long wait. More jam. More fuel use. More bad air.
Proof: `readme.md:32-35` says the system watches traffic with cameras and changes signal time to cut wait and jam.

You chose India, not a general case. You named three hard things in India:
a) drivers do not always follow lanes or stop lines,
b) rain and monsoon change the road,
c) roads have 3 ways, 4 ways, and 5 ways.
Proof: `docs/MASTER_PLAN.md:13-18`.

You built for weak and mixed hardware. Not only for one big machine. You wrote that Indian signals use many types of boxes, from old x86 boxes to Jetson TX2 to Orin NX to RK3588 NPU boxes.
Proof: `docs/MASTER_PLAN.md:31` row D5, and `configs/device.yaml:1-10` which sets three tiers: low, mid, high.

You added Indian vehicle types. You added AUTO for auto-rickshaw to the core types.
Proof: `src/adaptive_traffic/core/domain.py:11-17`.

You made city profiles. Mumbai has 4 lanes, aggressive_metro behaviour, heavy_monsoon weather. Bangalore has 3 lanes and light_rain. Delhi is balanced. There is also a tier2_default.
Proof: `config/city_profiles/mumbai.json:3-31`, and `docs/ARCHITECTURE.md:80-84`.

What this says about you: you do not run from hard real life. You pick the hard real case and you name it in writing.

## 2. How you work - your build method

### 2.1 You measure before you fix

Proved.

Phase 0 is Measure. It blocks all speed work. You first ran bench for sim and for detection, then you wrote the numbers down.
Proof: `docs/MASTER_PLAN.md:57-62`.

Result: sim did 28,503 steps per second. Target was only 500. So baseline was already 57 times above target.
Proof: `docs/BENCHMARKS.md:10` and `docs/MASTER_PLAN.md:196`.

What this says: you do not guess what is slow. You test, then you act.

### 2.2 You make one clear way to check work

Proved.

You deleted three old test runners. They were about 82KB of extra code that did the same job as pytest.
Proof: `docs/MASTER_PLAN.md:27` row D1.

You said Makefile targets are the ONLY check. No other way.
Proof: `AGENTS.md:14-23` lists loop-fast, verify, bench-sim, eval, graph-update, scan-skills, and gives the exact Windows commands.

Your gates are fixed numbers:
- make verify: 38 passed, 7 skipped
- make eval: 11 out of 11 adaptive wins
- bench_detect: 4.98 fps CPU int8
- bench_decide: 1.11ms p50 and 1.83ms p95 at 300 boxes
Proof: `AGENTS.md:51-56`.

What this says: you hate mess. You cut extra paths. You keep one door for truth.

### 2.3 You work in small done steps

Proved.

You have 8 phases plus a training track T. Each phase has an exit rule. Each done phase has a checkpoint file.
Proof: `docs/MASTER_PLAN.md:190-205` status board, and `checkpoints/` has phase0.done to phase6.done.

Git shows the same habit. Small commits with clear names:
- checkpoint phase0, phase1, phase2, phase3, phase4
- 8-loop chain plus finale
- monitoring steps 2 and 3
- TensorRT adapter as Phase 5 done
Proof: `git log --oneline` from 2026-08-26 to latest commit 0cd889a.

One session record says 33 files made or changed, with 20 new NTCIP tests, all passing.
Proof: `docs/TRACK_RECORD.md:9-11` and `docs/TRACK_RECORD.md:137-169`.

What this says: you finish in slices. Each slice can be checked.

### 2.4 You keep clean walls in code

Proved.

Your rule is short: `core/domain.py <- ports <- adapters`.
Proof: `AGENTS.md:99-103`.

What it means in easy words:
- domain = plain data shapes, no heavy libs.
- ports = empty plugs, only promises. Example: DetectorPort with detect(frame).
- adapters = real plugs that do the work. Example: OnnxDetector, UltralyticsDetector, TensorRTDetector.

Heavy libs live only inside adapters. OnnxDetector loads onnxruntime inside its own file, not at the top of the whole app.
Proof: `src/adaptive_traffic/core/detection/adapters_onnx.py:31` has `import onnxruntime` inside the class.

API and UI do not touch engine insides. They only use services and config.
Proof: `AGENTS.md:101-103` and `docs/ARCHITECTURE.md:61-72`.

What this says: you think about change. If hardware changes, only one small file changes.

### 2.5 You test against a fair enemy, not against nothing

Proved.

You made an eval matrix. 11 cases. Each case runs twice: adaptive plan and fixed-time plan. Same road, same cars, same rain. Then you compare.
Proof: `configs/evals/scenarios.yaml:1-10` and `docs/ARCHITECTURE.md:140-145`.

Result: adaptive wins 11 out of 11. Deltas from +2.9 percent to +79.6 percent. Headline: 5-way wait down 76.5 percent, 3-way down 31 percent.
Proof: `docs/BENCHMARKS.md:53-55` and `docs/BENCHMARKS.md:70-73`.

You also track time cost of the brain. Eval stores dec_p50 and dec_p95 in ms, with a flag if over 10ms.
Proof: `docs/BENCHMARKS.md:43-49`.

What this says: you do not claim good. You show good against a base line.

### 2.6 You train in a chain, not in one big bet

Proved.

Loop training: 8 loops, images_000 to images_007. Loop 1 starts from COCO with 20 epochs. Loops 2 to 8 start from last best and train 12 epochs each.
Proof: `AGENTS.md:42-49`.

Scores grew step by step on the same official val anchor: 0.7949 to 0.8041 to 0.8085 to 0.8155 to 0.8206 to 0.8249 to 0.8285 to 0.8293. No class went down in a bad way. Bicycle went 0.56 to 0.66.
Proof: `docs/BENCHMARKS.md:21` and `docs/MASTER_PLAN.md:218`.

Finale: 5 epochs, low learning rate 0.002, start from loop-8 best. Full 10k official val. Score 0.8477, up 0.0184. Per class: car 0.9189, auto 0.9171, moto 0.8887, bus 0.846, truck 0.8294, bicycle 0.6859.
Proof: `docs/BENCHMARKS.md:23-24` and `readme.md:20-24`.

You keep three registries: pilot, bmd chain winner, and final. Final is now the low-tier default.
Proof: `models/registry/` has india-yolov8n, india-yolov8n-bmd, india-yolov8n-final, and `configs/device.yaml:17` points low tier to india-yolov8n-final.

What this says: you are patient. You stack small wins. You keep old work as proof trail.

## 3. How you find weak points and use them

### 3.1 You list hard truths first

Proved.

Before you built, you wrote Current-State Findings. Examples: engine hard-codes 4-way phases so n-way is impossible today. Detector imports torch at top so no plug. VehicleType lacks AUTO. Perf tests are dead because they point to a deleted darkflow module.
Proof: `docs/MASTER_PLAN.md:38-53`.

You also wrote a premortem. That means you asked: how can this fail in six months. You kept the HTML report in the repo.
Proof: `docs/premortem-context.md:3` and `docs/premortem-report-2026-09-03.html`.

What this says: you look for holes on day one, not after launch.

### 3.2 You use weak points to set design

Proved. Four examples.

Example A - no real weather data. Fix: use a simple synthetic rain model now, but keep a clean plug WeatherSourcePort for a real IMD API later. Zero downstream change later.
Proof: `docs/MASTER_PLAN.md:29` row D3 and `docs/MASTER_PLAN.md:86-87`.

Example B - unknown edge box. Fix: do not lock to Orin. Use ONNX Runtime tiers: CPU int8, NPU, TensorRT fp16. Pick by YAML only.
Proof: `docs/MASTER_PLAN.md:31` row D5 and `configs/device.yaml:14-31`. Tiers still differ by runtime when model is shared, per `configs/device.yaml:8-10`.

Example C - weak low-tier box. Fix: now use interpolation only for queue gaps. Keep frame-skip plus background-subtraction as a future step, only if eval queue error goes above tolerance.
Proof: `docs/MASTER_PLAN.md:32` row D6.

Example D - 3, 4, 5-way roads. Fix: compatibility-graph scheduler. Roads that can go together share green. Empty roads are skipped. If no compat data, fall back to strict rotation.
Proof: `docs/MASTER_PLAN.md:34` row D7 and `docs/MASTER_PLAN.md:108-117`.

What this says: you turn a limit into a plug, a tier, or a fallback. You do not freeze.

### 3.3 You fix real wire bugs fast

Proved.

Wire tests found 2 real STMP bugs: OID BER set the continuation bit on wrong bytes, so every OID with 1206 was bad. And a full 4-phase SET crashed in struct.pack because about 300 bytes do not fit in a 1-byte length.
Proof: `docs/BENCHMARKS.md:130-136`.

You fixed base-128 continuation and BER long-form lengths the same day. You also wrote in the open that the real adapter had therefore never sent a full timing plan before the fix.
Proof: `docs/BENCHMARKS.md:135-136` and `docs/MASTER_PLAN.md:223`.

What this says: you let tests catch you. You admit it. You fix it.

### 3.4 You say no with numbers, and you write INCONCLUSIVE when true

Proved.

You skipped orjson. Reason: scorecards are about 6KB, payloads are tiny. Stdlib json stays. No new dep.
Proof: `docs/BENCHMARKS.md:140-141`.

You skipped uvloop. Reason: it does not install on the Windows dev host and there is no async hot loop. Use it later on Linux only if a profile proves need.
Proof: `docs/BENCHMARKS.md:142-144`.

You dropped estimator speed work. Reason: decide path at 300 boxes was 1.02ms p50 and 1.68ms p95. Budget is 10ms. Headroom is 6 times. Effort moved to durations and triggers.
Proof: `docs/BENCHMARKS.md:38-41` and `docs/MASTER_PLAN.md:219`.

Queue proxy test: detector found 0 of 576 rendered frames. RMSE 0.788 came from domain gap, not from your queue math. You wrote Trigger: INCONCLUSIVE, and hybrid trigger undecided, not fired.
Proof: `docs/BENCHMARKS.md:110-120`.

What this says: you do not chase speed or add libs for show. You stop when numbers say stop. You do not fake a win.

### 3.5 You change source when license or quality demands it

Proved.

You started with a HeTra pilot. Colab T4 mAP50 0.9816, auto 0.9744. Gate passed. But val covered only car, bus, auto. Full 6-class needs BMD-45.
Proof: `docs/BENCHMARKS.md:20`.

You switched to official iisc-aim BMD-45. It is CC-BY-4.0, OK for commercial use. 153 GB PNGs. You rewired the notebook to chunked PNG to JPG transcode and to the official 10k val split with no fake split.
Proof: `docs/MASTER_PLAN.md:214`.

Old kalyan1729 copy was marked superseded. Pilot metadata kept as provenance, but finale is canonical.
Proof: `docs/MASTER_PLAN.md:204` and `docs/MASTER_PLAN.md:221`.

What this says: you drop sunk work when a better legal and better quality source appears.

## 4. How you use limits as tools - loopholes you used well

Proved. This is not cheating. This is smart use of small doors.

1. Free Colab T4 instead of costly GPU. You split work: train on GPU in Colab, deploy anywhere with ONNX. Notebook is Drive-native, resume-safe, JPGs skipped if already done.
Proof: `AGENTS.md:31-40` and `AGENTS.md:70-73`.

2. Small model first. yolov8n first strategy. 3.0M params. 11.7 MB fp32 and 3.4 MB int8. Cheap to run, easy to ship.
Proof: `readme.md:22-23`.

3. Static int8 for CPU. Finale int8 runs 4.98 fps on CPU, 200.6ms per frame. Faster than loop-8 3.14 fps and pilot dynamic quant 0.68 fps.
Proof: `docs/BENCHMARKS.md:19-23`.

4. Sim is already fast, so you deferred heavy speed work. Vectorization deferred. Numba and Rust kept as later rungs only if wall-bound. Target 500 steps per second was already beaten 57 times.
Proof: `docs/BENCHMARKS.md:12-13` and `docs/MASTER_PLAN.md:202`.

5. Config instead of code for new cities and new roads. New city = new JSON. New road shape = new approach list plus compat matrix. No code change.
Proof: `config/city_profiles/mumbai.json:62-67` and `configs/evals/scenarios.yaml:26-40`.

6. Knowledge saved as skills. 58 skill folders. Project skills include signal-control-patterns, queue-estimation-patterns, robustness-eval-patterns, yolov8-tensorrt-patterns, traffic-simulation-patterns, jetson-deployment-patterns.
Proof: `.opencode/skill/` listing, and skill files like `.opencode/skill/queue-estimation-patterns/SKILL.md`.

What this says: you win by small cost, small model, small config change, and saved knowledge.

## 5. Your character as seen in the work

Each line is Proved unless marked Likely.

- Systems thinker. You build loops and machines, not one-off scripts. Proof: Makefile as single source, eval runner, bench scripts, checkpoints, auto-graph.
- Evidence-first. You ask for plan first and for no hallucination. Proof: your request for this document, plus BENCHMARKS honesty about INCONCLUSIVE and never-sent plan.
- Disciplined deleter. You deleted 82KB legacy runners and large graph history to keep the repo clean. Proof: MASTER_PLAN D1 and git commit fcde3a5 clean for production.
- Patient improver. 8 loops plus finale polish. Proof: BENCHMARKS chain 0.7949 to 0.8477.
- Honest writer. You keep maintenance rules that force docs to match reality after every phase. Proof: `docs/MASTER_PLAN.md:5-7` and `AGENTS.md:25-27`.
- User-aware. You added an Easy Start Guide for non-technical users, plus city profiles so field teams change JSON not code. Proof: `docs/EASY_START_GUIDE.md` exists, `Makefile:48-50` set-city help.
- Standard-keeper. Black line 100, isort black profile, flake8, mypy, bandit in CI. Proof: `pyproject.toml:146-196` and `TRACK_RECORD.md:118-124`.
- Self-critical. Premortem warns that eval is still synthetic, shares one queue estimator for both arms, and India incident taxonomy is not yet full scenarios. Proof: `docs/premortem-report-2026-09-03.html:136`.
- Likely: calm under block. When data was blocked, you built spec, converter, validator, calibration sampler, and notebook first, so you were data-ready. Proof: `docs/MASTER_PLAN.md:156-172` Phase T ready blocked on data.

## 6. Risks and blind spots seen in the repo - honest list

Proved. These are not insults. They are open items you already wrote.

1. No Jetson test yet. TensorRT code is complete with engine cache and fallback, but on-device latency validation is pending Jetson hardware. Proof: `docs/MASTER_PLAN.md:202`.
2. Real controller not tested. Closed loop works with mock STMP. `--ntcip-ip` to a real controller is untested. Proof: `docs/BENCHMARKS.md:124-128`.
3. STMP GET parse is still a stub. GET returns defaults. Proof: `docs/BENCHMARKS.md:136`.
4. No live camera thread yet. Pipeline has DropOldestBuffer and StagedPipeline, but no live caller. API serves mocks, sim is synthetic. Proof: `docs/BENCHMARKS.md:90-96`.
5. Rendered test frames are blind. 576 renders are near-black schematics, mean 0.47 labels per frame. Photo-trained model sees zero. First honest queue error needs phone footage plus hand counts. Proof: `docs/BENCHMARKS.md:25` and `docs/BENCHMARKS.md:115-120`.
6. Eval is synthetic. 11 scenarios use degraded confidence and latency to fake tiers. Real detector stream does not feed the matrix. Both arms share the same estimator, so it tests scheduling more than perception. Proof: premortem HTML line 136, and `docs/TESTING_DOCUMENTATION.md:50`.
7. Heavy import rule has one leak to check. Controllers file imports torch inside functions for DQN. That breaks the strict adapters-only idea unless it is moved. Proof: grep found `src/adaptive_traffic/core/control/controllers.py:295-296` and `:359` import torch.

## 7. What we do not know - no guess

Unknown. We do not have proof in the repo, so we stop here.

- Your age, job title, team size, or company.
- Why you personally care about traffic, beyond what docs say about India needs.
- How many hours you worked, or who helped you.
- Your skill outside this project, like web, mobile, or management.
- Your future goal beyond what you said in this one request: to become a top strategist.

## 8. Source table - where each claim comes from

- Vision and India edge cases: `docs/MASTER_PLAN.md:11-21`
- Locked choices D1 to D10: `docs/MASTER_PLAN.md:23-36`
- Start findings: `docs/MASTER_PLAN.md:38-53`
- Phase board and dates: `docs/MASTER_PLAN.md:190-223`
- Single check system: `AGENTS.md:14-27`
- Gates 38 passed 7 skipped, 11 of 11, 4.98 fps, 1.11 and 1.83ms: `AGENTS.md:51-56`
- Dependency walls: `AGENTS.md:99-103`
- Training chain and finale steps: `AGENTS.md:29-73`
- Bench sim 28,503 and target 500: `docs/BENCHMARKS.md:6-13`
- Detection fps rows and chain scores: `docs/BENCHMARKS.md:17-24`
- Decide path table and drop of estimator work: `docs/BENCHMARKS.md:27-41`
- Adaptive durations formula and 11 of 11 deltas: `docs/BENCHMARKS.md:43-55`
- Queue proxy INCONCLUSIVE: `docs/BENCHMARKS.md:105-120`
- Closed loop and STMP bugs: `docs/BENCHMARKS.md:122-136`
- Skips orjson and uvloop: `docs/BENCHMARKS.md:138-144`
- One session 33 files and NTCIP design: `docs/TRACK_RECORD.md:9-101`
- City values Mumbai Delhi Bangalore Tier2: `docs/ARCHITECTURE.md:80-93`
- Device tiers low mid high: `configs/device.yaml:1-31` and `docs/ARCHITECTURE.md:147-153`
- Class schema 6 classes and provisional flag: `docs/DATASET_SPEC.md:40-61`
- Eval scenarios shape: `configs/evals/scenarios.yaml:1-60`
- Domain AUTO and directions: `src/adaptive_traffic/core/domain.py:11-28`
- Onnx lazy import and registry via metadata: `src/adaptive_traffic/core/detection/adapters_onnx.py:19-39`
- Registry folders: `models/registry/` has india-yolov8n, india-yolov8n-bmd, india-yolov8n-final
- Skills count 58 and key skills: `.opencode/skill/` listing
- Git small steps: `git log --oneline` cca9f30 to 0cd889a
- Your request style: your prompt for this document asking for plan first, evidence only, no hallucination

---

End. This is who you are today, from proof only. No future map, per your choice.
