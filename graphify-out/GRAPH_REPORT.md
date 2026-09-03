# Graph Report - Adaptive-Traffic-Signal-Timer  (2026-09-03)

## Corpus Check
- 102 files · ~63,171 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1515 nodes · 2228 edges · 130 communities (83 shown, 34 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 126 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3d6c6de9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_settings
- VehicleDetection
- TrafficState
- TestAuthenticationSecurity
- TestVehicleClass
- conftest.py
- TrafficForecaster
- TestDetectionSimulationPipeline
- TrafficSimulation
- TestBoundaryConditions
- TestVehicleDetectionPerformance
- ProductionRunner
- detection.py
- signals.py
- 🚦 Easy Start Guide - Adaptive Traffic Signal Timer
- analytics.py
- 🎯 ADAPTIVE TRAFFIC SIGNAL TIMER - TOP 0.1% TESTING IMPLEMENTATION COMPLETE
- deploy.sh
- TestSimulationConstants
- TestVehicleDetectionEdgeCases
- TestDataEncryption
- TestVehicleDetectionModern
- src/ui/app.py
- test_enhanced_demo_components
- test_enhanced_gif
- test_gif_loading
- middleware/__init__.py
- config/__init__.py
- control/__init__.py
- detection/__init__.py
- core/__init__.py
- components/__init__.py
- .test_05_image_dimensions_extraction
- .test_07_random_detection_count_bounds
- .test_08_vehicle_types_definition
- .test_09_bounding_box_generation
- .test_10_confidence_score_range
- .setUpClass
- .test_12_rectangle_drawing_parameters
- .test_13_text_rendering_parameters
- .test_14_output_file_path_construction
- .test_15_image_writing_error_handling
- prepare_dataset.py
- .tearDownClass
- .test_17_output_formatting
- .test_19_directory_existence_check
- .test_20_output_directory_creation
- PredictiveAnalytics
- .test_22_no_images_handling
- .test_23_completion_message
- Dataset Specification — India-YOLO Training Data
- .test_03_global_variables_initialization
- .test_02_detectVehicles_function_exists
- DigitalTwin
- .test_04_image_loading_error_handling
- adaptive-traffic-signal
- RobustnessEvaluator
- 🚦 Adaptive Traffic Signal Timer
- 🚦 Enhanced Adaptive Traffic Signal Demo - Final Setup Guide
- Intersection
- 4. Phase Plan (execution order)
- engine.py
- forecaster.py
- NTCIPCycleConfig
- 🔧 Testing Methodology
- TestFileSystemSecurity
- test_vehicle_detection_unit.py
- TestInputValidation
- create_simulation
- TrafficForecast
- Adaptive Traffic Signal Timer - Testing Documentation
- test_security.py
- TestSimulationEdgeCases
- test_simulation_unit.py
- TestTrafficSignalClass
- TestVehicleMovement
- TestSignalTiming
- Benchmarks
- Jetro Agent Context
- **Line-by-Line Code Analysis**
- 🎯 System Readiness Assessment
- AGENTS.md
- 🚨 Critical Findings and Recommendations
- 📈 Test Metrics and KPIs
- 📋 Test Execution Checklist
- 🚀 Quick Start Guide
- **3. Performance Testing Strategy**
- 🔍 Code Analysis Examples
- CLAUDE.md
- .test_18_path_setup_variables
- SyntheticDatasetGenerator
- FuzzyController
- controllers.py
- FixedTimeController
- get
- TrafficRenderer
- 2026-09-02.md
- 2026-09-03.md
- NTCIPSNMPAdapter
- NTCIP1202STMPAdapter
- MockNTCIPSNMPAdapter
- Implementation Plan: India-Specific Adaptive Traffic Signal System
- J2735Adapter
- QueueEstimator
- CityProfile
- TestJ2735Adapter
- city_profile.py
- Premortem Context — Adaptive Traffic Signal Timer
- J2735MAP
- Device Tiers & Supported Hardware Matrix
- profile_device.py
- CityProfileRegistry
- OnnxDetector
- TestNTCIPSTMPAdapter
- 2026-09-03 — premortem
- bench_detect.py
- .detect

## God Nodes (most connected - your core abstractions)
1. `TrafficSimulation` - 41 edges
2. `CityProfile` - 40 edges
3. `NTCIPCycleConfig` - 32 edges
4. `TestVehicleDetectionModern` - 28 edges
5. `J2735Adapter` - 27 edges
6. `NTCIP1202STMPAdapter` - 26 edges
7. `VehicleDetection` - 26 edges
8. `get_settings()` - 25 edges
9. `NTCIPSNMPAdapter` - 24 edges
10. `NTCIPPhaseTiming` - 22 edges

## Surprising Connections (you probably didn't know these)
- `main()` --uses--> `DetectorPort`  [INFERRED]
  scripts/bench_detect.py → src/adaptive_traffic/core/detection/base.py
- `TrafficRenderer` --uses--> `VehicleDetection`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/domain.py
- `TrafficRenderer` --uses--> `Lane`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/engine.py
- `TrafficRenderer` --uses--> `TrafficSimulation`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/engine.py
- `TrafficRenderer` --uses--> `Vehicle`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/engine.py

## Import Cycles
- None detected.

## Communities (130 total, 34 thin omitted)

### Community 0 - "get_settings"
Cohesion: 0.05
Nodes (57): BaseSettings, datetime, FastAPI, create_app(), lifespan(), FastAPI Main Application, Application lifespan events, Create FastAPI application (+49 more)

### Community 1 - "VehicleDetection"
Cohesion: 0.10
Nodes (26): ONNX Detection Adapter CPU/NPU backend — loads models from…, create_detector(), MultiCameraDetector, ndarray, Ultralytics YOLO Detection Adapter Heavy imports (ultralytics, torch) are lazy,…, Detect vehicles in multiple frames, Multi-camera vehicle detection with fusion, Run detection on all cameras (+18 more)

### Community 2 - "TrafficState"
Cohesion: 0.17
Nodes (10): DQNController, Signal timing plan for one intersection, Deep Q-Network based adaptive signal controller, Convert traffic state to model input, Convert discrete action to green times, Current traffic state at intersection, Compute optimal signal timing given traffic state, Ensure value is within min/max green bounds (+2 more)

### Community 3 - "TestAuthenticationSecurity"
Cohesion: 0.18
Nodes (8): Test authentication and authorization security, Test: Password policy validation, Simulate password validation, Test: Session management security, Simulate session validation, Test: Access control validation, Simulate access control check, TestAuthenticationSecurity

### Community 4 - "TestVehicleClass"
Cohesion: 0.20
Nodes (5): Test: Line 102-156 - Vehicle class initialization, Test: Line 106 - Vehicle speed assignment, Test: Line 109-110 - Coordinate assignment, Test: Line 118-120 - Image loading, TestVehicleClass

### Community 5 - "conftest.py"
Cohesion: 0.19
Nodes (15): fixed_controller(), fuzzy_controller(), mock_detection(), mock_detections(), fixture, Shared pytest fixtures for Adaptive Traffic Signal Timer tests, Reset random seed for reproducible tests, Mock vehicle detection (+7 more)

### Community 6 - "TrafficForecaster"
Cohesion: 0.17
Nodes (8): create_forecaster(), Forecast single time series using seasonal naive + linear trend, Get recent average flow, Traffic flow forecasting using time series analysis, Factory function to create forecaster, Update historical data, Generate traffic forecast, TrafficForecaster

### Community 7 - "TestDetectionSimulationPipeline"
Cohesion: 0.05
Nodes (27): skip, Test that data flows without corruption, Test Streamlit dashboard integration, Test that dashboard can import required modules, Test dashboard page navigation structure, Test that dashboard can display real-time data, Test coordination between multiple modules, Test that modules maintain synchronized timing (+19 more)

### Community 8 - "TrafficSimulation"
Cohesion: 0.11
Nodes (12): Microscopic traffic simulation, Add intersection to simulation, Advance simulation by one time step, Update traffic signal states, Update lane signal states based on current phase group, Generate new vehicles based on rates, Update all vehicle positions and states, Remove vehicles that have passed through the intersection (+4 more)

### Community 9 - "TestBoundaryConditions"
Cohesion: 0.05
Nodes (25): Test: Extreme signal timing values, Test: Vehicle detection with boundary image sizes, Test: System behavior with extreme coordinate values, Test system behavior under resource exhaustion, Test: System behavior under memory exhaustion, Test boundary conditions and edge cases, Test: System behavior under CPU exhaustion, Test: System behavior with zero vehicles (+17 more)

### Community 10 - "TestVehicleDetectionPerformance"
Cohesion: 0.06
Nodes (22): skip, Test: Concurrent processing performance, Test: Performance with large images (4K), Performance tests for traffic simulation, Test: Simulation maintains 30+ FPS, Performance tests for vehicle detection module, Test: Performance with many vehicles, Set up test environment (+14 more)

### Community 11 - "ProductionRunner"
Cohesion: 0.08
Nodes (16): main(), ProductionRunner, Continuous health check loop, Check health of a specific endpoint, Collect and report application metrics, Collect application and system metrics, Production application runner with health checks and graceful shutdown, Send metrics to external monitoring system (+8 more)

### Community 12 - "detection.py"
Cohesion: 0.11
Nodes (27): CameraConfig, delete_camera(), detect_batch(), detect_vehicles(), DetectionResponse, DetectionResult, get_camera(), get_detection_history() (+19 more)

### Community 13 - "signals.py"
Cohesion: 0.08
Nodes (41): BSMQueueRefinement, create_timing_plan(), delete_timing_plan(), get_j2735_adapter(), get_ntcip_adapter(), get_ntcip_timing(), get_signal(), get_signal_health() (+33 more)

### Community 14 - "🚦 Easy Start Guide - Adaptive Traffic Signal Timer"
Cohesion: 0.05
Nodes (37): 🚦 Easy Start Guide - Adaptive Traffic Signal Timer, 🐧 **For Linux Users**, 🍎 **For Mac Users**, 🪟 **For Windows Users**, 🤝 Need More Help?, 🎯 Other Things You Can Try, **Part 1: Vehicle Detection**, **Part 2: Traffic Simulation** (+29 more)

### Community 15 - "analytics.py"
Cohesion: 0.23
Nodes (12): evaluate_scenario(), ForecastRequest, get_forecast(), ingest_sensor_data(), BaseModel, post, Analytics and forecasting endpoints, Get traffic forecast for intersection (+4 more)

### Community 16 - "🎯 ADAPTIVE TRAFFIC SIGNAL TIMER - TOP 0.1% TESTING IMPLEMENTATION COMPLETE"
Cohesion: 0.05
Nodes (36): **1. Line-by-Line Code Analysis Framework**, **2. Unit Testing with Necessity Assessment**, **3. Integration Testing Framework**, **4. Performance and Stress Testing**, **5. Security and Vulnerability Testing**, **6. Edge Case and Boundary Testing**, **7. Automated Test Runner**, **8. Test Execution Orchestrator** (+28 more)

### Community 17 - "deploy.sh"
Cohesion: 0.33
Nodes (15): build_images(), check_prerequisites(), check_service_health(), cleanup(), deploy_services(), health_check(), main(), print_error() (+7 more)

### Community 18 - "TestSimulationConstants"
Cohesion: 0.12
Nodes (9): Test: Line 60 - Vehicle speed dictionary, Test: Line 63-64 - Coordinate system initialization, Test: Line 66 - Vehicle data structure, Test simulation constants and global variables, Test: Line 27-31 - Default signal timing constants, Test: Line 33-40 - Signal configuration variables, Test: Line 43-47 - Vehicle timing constants, Test: Line 49-55 - Vehicle count variables (+1 more)

### Community 19 - "TestVehicleDetectionEdgeCases"
Cohesion: 0.25
Nodes (5): Edge case testing for vehicle detection module, Test handling of empty or corrupted images, Test handling of very small images, Test handling of very large images, TestVehicleDetectionEdgeCases

### Community 20 - "TestDataEncryption"
Cohesion: 0.24
Nodes (6): Test data encryption and protection, Test: Sensitive data handling, Simulate sensitive data masking, Test: Data transmission security, Check if transmission protocol is secure, TestDataEncryption

### Community 21 - "TestVehicleDetectionModern"
Cohesion: 0.15
Nodes (7): Test: Line 24-26 - Mock detection setup, Test: Line 42-47 - Detection dictionary structure, Comprehensive unit tests for vehicle_detection_modern.py, Test: Line 68-71 - Vehicle counting logic, Test: Line 102 - File filtering logic, Test: Line 1-5 - Module imports and structure, TestVehicleDetectionModern

### Community 42 - "prepare_dataset.py"
Cohesion: 0.44
Nodes (9): check(), _class_index(), convert_coco(), convert_yolo(), main(), make_calibration(), Path, Dataset normalizer/validator — enforces docs/DATASET_SPEC.md contract. Usage:… (+1 more)

### Community 47 - "PredictiveAnalytics"
Cohesion: 0.20
Nodes (6): PredictiveAnalytics, Main predictive analytics engine, Ingest real-time sensor data, Get traffic forecast for intersection, Evaluate what-if scenario, Get signal timing recommendations based on predictions

### Community 50 - "Dataset Specification — India-YOLO Training Data"
Cohesion: 0.22
Nodes (8): 1. Layout, 2. Class schema, 3. Label format, 4. Split hygiene (non-negotiable), 5. Capture metadata (`meta/captures.json`), 6. Quantization calibration set, 7. Acceptance checklist (run automatically), Dataset Specification — India-YOLO Training Data

### Community 53 - "DigitalTwin"
Cohesion: 0.25
Nodes (5): DigitalTwin, Infrastructure Digital Twin for real-time simulation, Update digital twin state from real sensors, Detect anomalies in traffic data, Simulate what-if scenario

### Community 58 - "RobustnessEvaluator"
Cohesion: 0.10
Nodes (17): create_robustness_evaluator(), IncidentScenario, Robustness Evaluation Evaluates controller performance under various incidents…, Simulate power outage - force fixed-time control, Simulate adverse weather, Run robustness evaluation for all incidents, Run simulation with controller and return average waiting time, Get summary statistics (+9 more)

### Community 66 - "🚦 Adaptive Traffic Signal Timer"
Cohesion: 0.07
Nodes (28): 🙏 Acknowledgments, 🚦 Adaptive Traffic Signal Timer, 🏗️ Architecture, Code Standards, 🔧 Configuration, 🤝 Contributing, Development Setup, Environment Variables (+20 more)

### Community 67 - "🚦 Enhanced Adaptive Traffic Signal Demo - Final Setup Guide"
Cohesion: 0.08
Nodes (24): 1. **System Overview**, 2. **Live Interactive Demo**, 3. **Algorithm Comparison**, 4. **Impact Metrics**, 5. **Advanced Features**, 🎨 Demo Features, Economic Value, 🚦 Enhanced Adaptive Traffic Signal Demo - Final Setup Guide (+16 more)

### Community 68 - "Intersection"
Cohesion: 0.14
Nodes (18): Direction, Enum, VehicleType, create_intersection(), _default_compatibility_groups(), Intersection, Lane, Vehicle in simulation (+10 more)

### Community 69 - "4. Phase Plan (execution order)"
Cohesion: 0.11
Nodes (18): 1. Project Vision, 2. Locked Decisions, 3. Current-State Findings (verified 2026-08-26), 4. Phase Plan (execution order), 5. Success Criteria (overall), 6. Out of Scope (explicitly deferred), 7. Phase Status Board, 8. Change Log (+10 more)

### Community 70 - "engine.py"
Cohesion: 0.11
Nodes (15): Random, BehaviorEngine, DisciplineProfile, profile_for(), Vehicle Behavior Profiles for Heterogeneous Traffic Simulation, Applies behavioral anomalies to vehicles via a seeded rng, Behavioral discipline parameters for a vehicle class, Per-class adjusted copy of the typical_urban baseline (+7 more)

### Community 71 - "forecaster.py"
Cohesion: 0.33
Nodes (5): create_digital_twin(), create_predictive_analytics(), Predictive Analytics Module, Factory function to create digital twin, Factory function to create predictive analytics engine

### Community 72 - "NTCIPCycleConfig"
Cohesion: 0.06
Nodes (26): STMP operation - not supported in SNMP adapter, STMP operation - not supported in SNMP adapter, MockNTCIP1202STMPAdapter, NTCIP 1202 STMP Adapter Actuation via NTCIP 1202 Standard for Signal Control…, Apply phase timing via NTCIP 1202 STMP SET, Get current phase timing via NTCIP 1202 STMP GET, Build NTCIPCycleConfig from parsed response, Mock STMP adapter for testing without real controller (+18 more)

### Community 73 - "🔧 Testing Methodology"
Cohesion: 0.15
Nodes (13): **1. Unit Testing Strategy**, **2. Integration Testing Strategy**, **4. Security Testing Strategy**, **5. Edge Case Testing Strategy**, **Boundary Conditions**, **Data Flow Validation**, **File System Security**, **Input Validation** (+5 more)

### Community 74 - "TestFileSystemSecurity"
Cohesion: 0.17
Nodes (8): skip, Test file system security and access controls, Test: Directory traversal attack prevention, Test: File permission validation, Test: Temporary file cleanup, Test: File upload validation (if applicable), Simulate file upload validation, TestFileSystemSecurity

### Community 75 - "test_vehicle_detection_unit.py"
Cohesion: 0.40
Nodes (3): Performance tests for vehicle detection module, Test that processing time is within acceptable limits, TestVehicleDetectionPerformance

### Community 76 - "TestInputValidation"
Cohesion: 0.17
Nodes (7): Test: SQL injection prevention (if database is used), Test: Cross-site scripting prevention in web interface, Test input validation and sanitization, Test: Filename input validation prevents path traversal, Test: Image format validation prevents malicious files, Test: Command injection prevention in subprocess calls, TestInputValidation

### Community 77 - "create_simulation"
Cohesion: 0.24
Nodes (9): _apply_incident(), _load_scenarios(), main(), Eval matrix runner: adaptive vs fixed-time baseline across scenario YAMLs., run_scenario(), bench(), Simulation throughput benchmark — fixed seed, standard config., create_simulation() (+1 more)

### Community 78 - "TrafficForecast"
Cohesion: 0.50
Nodes (3): Traffic flow forecast, Get current traffic predictions, TrafficForecast

### Community 79 - "Adaptive Traffic Signal Timer - Testing Documentation"
Cohesion: 0.22
Nodes (8): Adaptive Traffic Signal Timer - Testing Documentation, 🎉 Conclusion, **Core Testing Categories**, **Documentation Updates**, 📞 Support and Maintenance, **Test Maintenance**, 📋 Testing Framework Overview, 🎯 Top 0.1% Expert Testing Team Implementation

### Community 80 - "test_security.py"
Cohesion: 0.25
Nodes (5): Test logging security and information disclosure, Test: No sensitive information in logs, Test: Log injection prevention, Simulate log entry sanitization, TestLoggingSecurity

### Community 81 - "TestSimulationEdgeCases"
Cohesion: 0.25
Nodes (5): Edge case testing for simulation, Test simulation with no vehicles, Test simulation with maximum vehicles, Test behavior when signal fails, TestSimulationEdgeCases

### Community 82 - "test_simulation_unit.py"
Cohesion: 0.29
Nodes (4): Performance tests for simulation, Test that simulation maintains acceptable frame rate, Test memory usage with many vehicles, TestSimulationPerformance

### Community 83 - "TestTrafficSignalClass"
Cohesion: 0.29
Nodes (4): Test TrafficSignal class, Test: Line 92-99 - TrafficSignal class initialization, Test TrafficSignal parameter validation, TestTrafficSignalClass

### Community 84 - "TestVehicleMovement"
Cohesion: 0.29
Nodes (4): Test vehicle movement logic, Test: Line 162-189 - Right direction movement logic, Test: Line 166-178 - Vehicle turning behavior, TestVehicleMovement

### Community 85 - "TestSignalTiming"
Cohesion: 0.29
Nodes (4): Test signal timing algorithms, Test: Line 280-323 - setTime function logic, Test: Line 325-357 - repeat function logic, TestSignalTiming

### Community 86 - "Benchmarks"
Cohesion: 0.33
Nodes (5): Benchmarks, Detection (`make bench-detect`), Eval Matrix (`make eval`), Sim Throughput (`make bench-sim`), Test Suite Wall Time

### Community 87 - "Jetro Agent Context"
Cohesion: 0.40
Nodes (4): Available Skills, Available Templates, Getting Started, Jetro Agent Context

### Community 88 - "**Line-by-Line Code Analysis**"
Cohesion: 0.40
Nodes (5): **Contribution Analysis**, **Line-by-Line Code Analysis**, **Necessity Assessment**, **Optimization Opportunities**, 📊 Test Coverage Analysis

### Community 89 - "🎯 System Readiness Assessment"
Cohesion: 0.40
Nodes (5): **Near Production Ready** ⚠️, **Needs Improvement** ⚠️, **Not Ready** ❌, **Production Ready** ✅, 🎯 System Readiness Assessment

### Community 90 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): Dependency rule, graphify, Verification (single source of truth)

### Community 91 - "🚨 Critical Findings and Recommendations"
Cohesion: 0.50
Nodes (4): 🚨 Critical Findings and Recommendations, **Immediate Actions Required**, **Long-term Enhancements**, **Short-term Improvements**

### Community 92 - "📈 Test Metrics and KPIs"
Cohesion: 0.50
Nodes (4): **Performance Metrics**, **Quality Metrics**, **Security Metrics**, 📈 Test Metrics and KPIs

### Community 93 - "📋 Test Execution Checklist"
Cohesion: 0.50
Nodes (4): **Post-Test Analysis**, **Pre-Test Setup**, **Test Execution**, 📋 Test Execution Checklist

### Community 94 - "🚀 Quick Start Guide"
Cohesion: 0.50
Nodes (4): 🚀 Quick Start Guide, **Run All Tests**, **Run Individual Test Files**, **Run Specific Test Categories**

### Community 95 - "**3. Performance Testing Strategy**"
Cohesion: 0.67
Nodes (3): **3. Performance Testing Strategy**, **Load Testing Scenarios**, **Stress Testing**

### Community 96 - "🔍 Code Analysis Examples"
Cohesion: 0.67
Nodes (3): 🔍 Code Analysis Examples, **Line-by-Line Analysis Sample**, **Quality Assessment Sample**

### Community 99 - "SyntheticDatasetGenerator"
Cohesion: 0.12
Nodes (14): CaptureMeta, main(), Path, Deterministic split by junction-day index (no random frame splitting)., Create simulation with specified configuration., Generate frames for a specific configuration., Apply realistic augmentations., Save image and label file. (+6 more)

### Community 100 - "FuzzyController"
Cohesion: 0.23
Nodes (4): FuzzyController, Fuzzy logic signal controller, Define fuzzy membership functions and rules, Fuzzy inference for green time adjustment

### Community 101 - "controllers.py"
Cohesion: 0.23
Nodes (10): BaseController, ControllerType, create_controller(), ABC, Enum, Signal Control Algorithms, Webster's method for optimal cycle length and green split, Factory function to create signal controller Args: controller_type: Type of… (+2 more)

### Community 102 - "FixedTimeController"
Cohesion: 0.20
Nodes (4): FixedTimeController, Switch to a different timing plan, Build or load DQN model, Fixed-time signal controller with pre-defined timing plans

### Community 103 - "get"
Cohesion: 0.22
Nodes (9): get_environmental_impact(), get_metrics(), get_performance(), get_recommendations(), get, Get performance analytics, Get environmental impact metrics, Get signal timing recommendations (+1 more)

### Community 107 - "TrafficRenderer"
Cohesion: 0.23
Nodes (8): ndarray, Renders simulation state to image with YOLO bounding boxes., Convert world coordinates (meters) to image pixels., Render a simulation frame and return image + detections., Draw vehicle and return YOLO detection., Apply weather visual effects., Apply time-of-day lighting (simplified)., TrafficRenderer

### Community 110 - "NTCIPSNMPAdapter"
Cohesion: 0.06
Nodes (37): create_j2735_adapter(), create_ntcip_adapter(), create_ntcip_snmp_adapter(), create_ntcip_stmp_adapter(), NTCIP/J2735 Adapters Package Factory functions for creating NTCIP and J2735…, Factory function to create NTCIP 1202 STMP adapter Args: config: Configuration…, Factory function to create NTCIP SNMP adapter Args: config: Configuration dict…, Factory function to create composite NTCIP adapter (STMP + SNMP) Args: config:… (+29 more)

### Community 111 - "NTCIP1202STMPAdapter"
Cohesion: 0.10
Nodes (12): NTCIP1202STMPAdapter, socket, Build SNMP varbind for STMP payload, Send STMP request and return response, Parse STMP response and return dict of OID -> value, NTCIP 1202 STMP adapter for signal controller actuation, Check if controller is reachable via STMP, Close the STMP socket (+4 more)

### Community 112 - "MockNTCIPSNMPAdapter"
Cohesion: 0.12
Nodes (9): MockNTCIPSNMPAdapter, SNMP GETNEXT request for table walking, Get detector status via SNMP GETNEXT, Get active faults via SNMP, Get cycle counters via SNMP, Check if controller is reachable via SNMP, Mock SNMP adapter for testing without real controller, Override mock SNMP GET with detector data (+1 more)

### Community 113 - "Implementation Plan: India-Specific Adaptive Traffic Signal System"
Cohesion: 0.09
Nodes (22): City Profile Schema (Core Fields), Cross-Cutting Tasks, Dependency Graph, Implementation Plan: India-Specific Adaptive Traffic Signal System, Key Design Decisions, Key Design Decisions, Key Design Decisions, Priority 1: NTCIP/J2735 V2X Adapter (`src/adaptive_traffic/adapters/ntcip.py`) (+14 more)

### Community 114 - "J2735Adapter"
Cohesion: 0.06
Nodes (28): BSMVehicleData, J2735Adapter, MockJ2735Adapter, socket, J2735 V2X Adapter Encoder/decoder for J2735 2020 messages: - BSM (Basic Safety…, Receive BSM messages from connected vehicles, Decode raw BSM payload (UPER encoded per J2735), Parse BSM into vehicle data for queue length refinement (+20 more)

### Community 115 - "QueueEstimator"
Cohesion: 0.10
Nodes (18): create_queue_estimator(), LaneQueue, QueueEstimate, QueueEstimator, Queue Length Estimator Converts vehicle detections to per-lane queue lengths…, Group detections by lane using bbox position and calibration, Estimate lane index from bounding box horizontal position, Estimate approach direction from bounding box vertical position (+10 more)

### Community 116 - "CityProfile"
Cohesion: 0.12
Nodes (20): CityProfile, Config, get_city_profile(), list_city_profiles(), Get city profile by name, List available city profiles, Complete city profile configuration, get_builtin_city_profile() (+12 more)

### Community 117 - "TestJ2735Adapter"
Cohesion: 0.10
Nodes (10): fixture, Test NTCIP SNMP adapter (monitoring), Test SNMP detector status retrieval, Test SNMP fault retrieval, Test SNMP cycle counter retrieval, Test SNMP connection check, Test J2735 V2X adapter (BSM receive, SPAT transmit), Test BSM-based queue refinement (+2 more)

### Community 118 - "city_profile.py"
Cohesion: 0.15
Nodes (18): DetectorCalibration, IncidentWeights, IntersectionGeometry, NTCIPConfig, BaseModel, City Profile Schema Pydantic models for city-specific configuration, Vehicle lengths in meters per class, Vehicle mix weights for spawning (must sum to 1.0) (+10 more)

### Community 119 - "Premortem Context — Adaptive Traffic Signal Timer"
Cohesion: 0.25
Nodes (7): Current evidence base, Locked decisions shaping the remaining path, Premortem Context — Adaptive Traffic Signal Timer, Remaining work (the plan under test), What does success look like?, What is it?, Who is it for?

### Community 120 - "J2735MAP"
Cohesion: 0.12
Nodes (11): Load static MAP data for intersection, Load MAP from city profile geometry, J2735MAP, Load static MAP data for intersection Args: map_data: Intersection geometry map…, J2735 Map Data (static intersection geometry), NTCIP Integration Tests Tests for NTCIP 1202 STMP actuation, SNMP monitoring,…, Test NTCIP/J2735 encoding/decoding utilities, Test NTCIPPhaseTiming dataclass (+3 more)

### Community 121 - "Device Tiers & Supported Hardware Matrix"
Cohesion: 0.29
Nodes (6): Device Matrix (Indian deployments), Device Tiers & Supported Hardware Matrix, Reproducing a Tier Baseline, Tier Definitions, Tier Selection Logic (`scripts/profile_device.py`), Upgrade Trigger: Tier-Low Hybrid Detector (Future)

### Community 122 - "profile_device.py"
Cohesion: 0.47
Nodes (5): detect_tier(), main(), Path, Hardware tier profiler — detects capability and writes active_tier to…, write_tier()

### Community 123 - "CityProfileRegistry"
Cohesion: 0.18
Nodes (8): CityProfileRegistry, Registry for city profiles with JSON file loading, Load built-in profiles as fallback, Load profiles from JSON files, Get city profile by name, Get city profile or return default, List available city profiles, Reload profiles from disk

### Community 124 - "OnnxDetector"
Cohesion: 0.29
Nodes (5): OnnxDetector, DetectionResult, ndarray, ONNX Runtime vehicle detector (CPU/NPU providers), Get confidence threshold for a class

### Community 125 - "TestNTCIPSTMPAdapter"
Cohesion: 0.17
Nodes (6): Test NTCIP 1202 STMP adapter (actuation), Test STMP SET operation for phase timing, Test STMP GET operation for phase timing, Test connection check, Test full STMP round-trip: SET then GET, TestNTCIPSTMPAdapter

### Community 126 - "2026-09-03 — premortem"
Cohesion: 0.40
Nodes (4): 2026-09-03 — premortem, 3-sentence summary, Failure reasons (9) — probability/impact, Revisions R1–R6 & checklist C1–C5

### Community 127 - "bench_detect.py"
Cohesion: 0.50
Nodes (4): main(), ndarray, Detection latency benchmark — CPU baseline via the configured DetectorPort…, synth_frames()

### Community 128 - ".detect"
Cohesion: 0.50
Nodes (3): DetectionResult, ndarray, Detect vehicles in a single frame

## Knowledge Gaps
- **200 isolated node(s):** `adaptive-traffic-signal`, `Config`, `Why First`, `Tasks`, `Key Design Decisions` (+195 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 775 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TrafficSimulation` connect `TrafficSimulation` to `SyntheticDatasetGenerator`, `Intersection`, `engine.py`, `TrafficRenderer`, `create_simulation`, `CityProfile`, `RobustnessEvaluator`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `CityProfile` connect `CityProfile` to `VehicleDetection`, `Intersection`, `controllers.py`, `engine.py`, `TrafficSimulation`, `create_simulation`, `QueueEstimator`, `city_profile.py`, `RobustnessEvaluator`, `CityProfileRegistry`, `OnnxDetector`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `NTCIPCycleConfig` connect `NTCIPCycleConfig` to `signals.py`, `NTCIPSNMPAdapter`, `NTCIP1202STMPAdapter`, `TestJ2735Adapter`, `J2735MAP`, `TestNTCIPSTMPAdapter`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `TrafficSimulation` (e.g. with `SyntheticDatasetGenerator` and `TrafficRenderer`) actually correct?**
  _`TrafficSimulation` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `CityProfile` (e.g. with `CityProfileRegistry` and `get_builtin_city_profile()`) actually correct?**
  _`CityProfile` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `NTCIPCycleConfig` (e.g. with `NTCIPSNMPAdapter` and `MockNTCIP1202STMPAdapter`) actually correct?**
  _`NTCIPCycleConfig` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `J2735Adapter` (e.g. with `J2735BSM` and `J2735MAP`) actually correct?**
  _`J2735Adapter` has 3 INFERRED edges - model-reasoned connections that need verification._