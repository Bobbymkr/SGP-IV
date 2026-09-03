# ProductionRunner

> 31 nodes · cohesion 0.08

## Key Concepts

- **ProductionRunner** (17 connections) — `scripts/run_production.py`
- **._metrics_collection_loop()** (5 connections) — `scripts/run_production.py`
- **.start_application()** (5 connections) — `scripts/run_production.py`
- **._health_check_loop()** (4 connections) — `scripts/run_production.py`
- **main()** (3 connections) — `scripts/run_production.py`
- **._check_endpoint_health()** (3 connections) — `scripts/run_production.py`
- **._collect_metrics()** (3 connections) — `scripts/run_production.py`
- **.graceful_shutdown()** (3 connections) — `scripts/run_production.py`
- **._load_config()** (3 connections) — `scripts/run_production.py`
- **._send_metrics_to_monitoring()** (3 connections) — `scripts/run_production.py`
- **._setup_signal_handlers()** (3 connections) — `scripts/run_production.py`
- **run_production.py** (2 connections) — `scripts/run_production.py`
- **._cleanup()** (2 connections) — `scripts/run_production.py`
- **.database_session()** (2 connections) — `scripts/run_production.py`
- **.get_application_info()** (2 connections) — `scripts/run_production.py`
- **.__init__()** (2 connections) — `scripts/run_production.py`
- **.redis_session()** (2 connections) — `scripts/run_production.py`
- **Continuous health check loop** (1 connections) — `scripts/run_production.py`
- **Check health of a specific endpoint** (1 connections) — `scripts/run_production.py`
- **Collect and report application metrics** (1 connections) — `scripts/run_production.py`
- **Collect application and system metrics** (1 connections) — `scripts/run_production.py`
- **Send metrics to external monitoring system** (1 connections) — `scripts/run_production.py`
- **Production application runner with health checks and graceful shutdown** (1 connections) — `scripts/run_production.py`
- **Setup signal handlers for graceful shutdown** (1 connections) — `scripts/run_production.py`
- **Perform graceful shutdown** (1 connections) — `scripts/run_production.py`
- *... and 6 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `scripts/run_production.py`

## Audit Trail

- EXTRACTED: 39 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
