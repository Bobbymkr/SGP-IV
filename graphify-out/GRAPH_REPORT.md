# Graph Report - Adaptive-Traffic-Signal-Timer  (2026-09-03)

## Corpus Check
- 77 files · ~43,494 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1073 nodes · 1436 edges · 109 communities (76 shown, 33 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 38 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2cd1fffe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_settings
- VehicleDetection
- TrafficState
- TestAuthenticationSecurity
- TestVehicleClass
- conftest.py
- datetime
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
- 🚦 Adaptive Traffic Signal Timer
- 🚦 Enhanced Adaptive Traffic Signal Demo - Final Setup Guide
- Intersection
- 4. Phase Plan (execution order)
- engine.py
- forecaster.py
- WeatherModel
- 🔧 Testing Methodology
- TestFileSystemSecurity
- test_vehicle_detection_unit.py
- TestInputValidation
- create_intersection
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
- domain.py
- 2026-09-02.md

## God Nodes (most connected - your core abstractions)
1. `TrafficSimulation` - 33 edges
2. `TestVehicleDetectionModern` - 28 edges
3. `get_settings()` - 22 edges
4. `VehicleDetection` - 21 edges
5. `SyntheticDatasetGenerator` - 17 edges
6. `ProductionRunner` - 17 edges
7. `TrafficRenderer` - 15 edges
8. `FuzzyController` - 14 edges
9. `🚦 Adaptive Traffic Signal Timer` - 14 edges
10. `OnnxDetector` - 13 edges

## Surprising Connections (you probably didn't know these)
- `TrafficRenderer` --uses--> `VehicleDetection`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/domain.py
- `TrafficRenderer` --uses--> `Lane`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/engine.py
- `TrafficRenderer` --uses--> `TrafficSimulation`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/engine.py
- `TrafficRenderer` --uses--> `Vehicle`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/engine.py
- `TrafficRenderer` --uses--> `WeatherState`  [INFERRED]
  scripts/generate_synthetic_dataset.py → src/adaptive_traffic/core/simulation/weather.py

## Import Cycles
- None detected.

## Communities (109 total, 33 thin omitted)

### Community 0 - "get_settings"
Cohesion: 0.05
Nodes (56): BaseSettings, FastAPI, create_app(), lifespan(), FastAPI Main Application, Application lifespan events, Create FastAPI application, health_check() (+48 more)

### Community 1 - "VehicleDetection"
Cohesion: 0.09
Nodes (27): OnnxDetector, DetectionResult, ndarray, ONNX Detection Adapter CPU/NPU backend — loads models from…, ONNX Runtime vehicle detector (CPU/NPU providers), create_detector(), MultiCameraDetector, ndarray (+19 more)

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
Cohesion: 0.17
Nodes (17): fixture, fixed_controller(), fuzzy_controller(), mock_detection(), mock_detections(), Shared pytest fixtures for Adaptive Traffic Signal Timer tests, Sample traffic simulation, Reset random seed for reproducible tests (+9 more)

### Community 6 - "datetime"
Cohesion: 0.21
Nodes (7): datetime, Forecast single time series using seasonal naive + linear trend, Get recent average flow, Traffic flow forecasting using time series analysis, Update historical data, Generate traffic forecast, TrafficForecaster

### Community 7 - "TestDetectionSimulationPipeline"
Cohesion: 0.05
Nodes (27): skip, Test that data flows without corruption, Test Streamlit dashboard integration, Test that dashboard can import required modules, Test dashboard page navigation structure, Test that dashboard can display real-time data, Test coordination between multiple modules, Test that modules maintain synchronized timing (+19 more)

### Community 8 - "TrafficSimulation"
Cohesion: 0.13
Nodes (10): Microscopic traffic simulation, Add intersection to simulation, Advance simulation by one time step, Generate new vehicles based on rates, Update all vehicle positions and states, Remove vehicles that have passed through the intersection, Update simulation statistics including queue observability., Get current state of an intersection (+2 more)

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
Cohesion: 0.12
Nodes (23): create_timing_plan(), delete_timing_plan(), get_signal(), get_signal_status(), get_timing_plan(), list_signals(), list_timing_plans(), BaseModel (+15 more)

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
Cohesion: 0.17
Nodes (8): create_predictive_analytics(), PredictiveAnalytics, Main predictive analytics engine, Ingest real-time sensor data, Get traffic forecast for intersection, Evaluate what-if scenario, Get signal timing recommendations based on predictions, Factory function to create predictive analytics engine

### Community 50 - "Dataset Specification — India-YOLO Training Data"
Cohesion: 0.22
Nodes (8): 1. Layout, 2. Class schema, 3. Label format, 4. Split hygiene (non-negotiable), 5. Capture metadata (`meta/captures.json`), 6. Quantization calibration set, 7. Acceptance checklist (run automatically), Dataset Specification — India-YOLO Training Data

### Community 53 - "DigitalTwin"
Cohesion: 0.25
Nodes (5): DigitalTwin, Infrastructure Digital Twin for real-time simulation, Update digital twin state from real sensors, Detect anomalies in traffic data, Simulate what-if scenario

### Community 66 - "🚦 Adaptive Traffic Signal Timer"
Cohesion: 0.07
Nodes (28): 🙏 Acknowledgments, 🚦 Adaptive Traffic Signal Timer, 🏗️ Architecture, Code Standards, 🔧 Configuration, 🤝 Contributing, Development Setup, Environment Variables (+20 more)

### Community 67 - "🚦 Enhanced Adaptive Traffic Signal Demo - Final Setup Guide"
Cohesion: 0.08
Nodes (24): 1. **System Overview**, 2. **Live Interactive Demo**, 3. **Algorithm Comparison**, 4. **Impact Metrics**, 5. **Advanced Features**, 🎨 Demo Features, Economic Value, 🚦 Enhanced Adaptive Traffic Signal Demo - Final Setup Guide (+16 more)

### Community 68 - "Intersection"
Cohesion: 0.17
Nodes (9): Intersection, Lane, Update traffic signal states, Pick next phase: demand-responsive when adaptive, round-robin otherwise., Update lane signal states based on current phase group, Update vehicles in a single lane, Move vehicle into an adjacent lane of the same direction if space allows., Calculate target speed for a vehicle (+1 more)

### Community 69 - "4. Phase Plan (execution order)"
Cohesion: 0.11
Nodes (18): 1. Project Vision, 2. Locked Decisions, 3. Current-State Findings (verified 2026-08-26), 4. Phase Plan (execution order), 5. Success Criteria (overall), 6. Out of Scope (explicitly deferred), 7. Phase Status Board, 8. Change Log (+10 more)

### Community 70 - "engine.py"
Cohesion: 0.19
Nodes (10): Random, BehaviorEngine, DisciplineProfile, profile_for(), Vehicle Behavior Profiles for Heterogeneous Traffic Simulation, Applies behavioral anomalies to vehicles via a seeded rng, Behavioral discipline parameters for a vehicle class, Per-class adjusted copy of the typical_urban baseline (+2 more)

### Community 71 - "forecaster.py"
Cohesion: 0.33
Nodes (5): create_digital_twin(), create_forecaster(), Predictive Analytics Module, Factory function to create forecaster, Factory function to create digital twin

### Community 72 - "WeatherModel"
Cohesion: 0.18
Nodes (5): Enum, Stochastic weather model with India monsoon seasonality, WeatherModel, WeatherProfile, WeatherState

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

### Community 77 - "create_intersection"
Cohesion: 0.14
Nodes (14): _apply_incident(), _load_scenarios(), main(), Eval matrix runner: adaptive vs fixed-time baseline across scenario YAMLs., run_scenario(), bench(), Simulation throughput benchmark — fixed seed, standard config., Create simulation with specified configuration. (+6 more)

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
Cohesion: 0.09
Nodes (21): CaptureMeta, main(), ndarray, Path, Renders simulation state to image with YOLO bounding boxes., Convert world coordinates (meters) to image pixels., Render a simulation frame and return image + detections., Draw vehicle and return YOLO detection. (+13 more)

### Community 100 - "FuzzyController"
Cohesion: 0.23
Nodes (4): FuzzyController, Fuzzy logic signal controller, Define fuzzy membership functions and rules, Fuzzy inference for green time adjustment

### Community 101 - "controllers.py"
Cohesion: 0.23
Nodes (10): BaseController, ControllerType, create_controller(), ABC, Enum, Signal Control Algorithms, Factory function to create signal controller, Base class for signal controllers (+2 more)

### Community 102 - "FixedTimeController"
Cohesion: 0.20
Nodes (4): FixedTimeController, Build or load DQN model, Fixed-time signal controller with pre-defined timing plans, Switch to a different timing plan

### Community 103 - "get"
Cohesion: 0.22
Nodes (9): get_environmental_impact(), get_metrics(), get_performance(), get_recommendations(), get, Get performance analytics, Get environmental impact metrics, Get signal timing recommendations (+1 more)

### Community 107 - "domain.py"
Cohesion: 0.23
Nodes (10): Direction, Enum, Shared Domain Types Single source of truth for cross-module dataclasses and…, Signal timing plan for one intersection, Current traffic state at intersection, SignalTiming, TrafficState, VehicleType (+2 more)

## Knowledge Gaps
- **166 isolated node(s):** `adaptive-traffic-signal`, `graphify`, `Verification (single source of truth)`, `Dependency rule`, `graphify` (+161 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_simulation()` connect `get_settings` to `TestDetectionSimulationPipeline`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `VehicleDetection` connect `VehicleDetection` to `domain.py`, `SyntheticDatasetGenerator`, `conftest.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `TrafficSimulation` (e.g. with `SyntheticDatasetGenerator` and `TrafficRenderer`) actually correct?**
  _`TrafficSimulation` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `VehicleDetection` (e.g. with `SyntheticDatasetGenerator` and `TrafficRenderer`) actually correct?**
  _`VehicleDetection` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SyntheticDatasetGenerator` (e.g. with `VehicleDetection` and `TrafficSimulation`) actually correct?**
  _`SyntheticDatasetGenerator` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `adaptive-traffic-signal`, `graphify`, `Verification (single source of truth)` to the rest of the system?**
  _166 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `get_settings` be split into smaller, more focused modules?**
  _Cohesion score 0.051360842844600525 - nodes in this community are weakly interconnected._