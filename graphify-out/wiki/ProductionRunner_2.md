# ProductionRunner

> God node · 17 connections · `scripts/run_production.py`

**Community:** [ProductionRunner](ProductionRunner.md)

## Connections by Relation

### calls
- [main()](main.md) `EXTRACTED`

### contains
- run_production.py `EXTRACTED`

### method
- ._metrics_collection_loop() `EXTRACTED`
- .start_application() `EXTRACTED`
- ._health_check_loop() `EXTRACTED`
- ._check_endpoint_health() `EXTRACTED`
- ._collect_metrics() `EXTRACTED`
- ._send_metrics_to_monitoring() `EXTRACTED`
- ._setup_signal_handlers() `EXTRACTED`
- .graceful_shutdown() `EXTRACTED`
- ._load_config() `EXTRACTED`
- .__init__() `EXTRACTED`
- ._cleanup() `EXTRACTED`
- .database_session() `EXTRACTED`
- .redis_session() `EXTRACTED`
- .get_application_info() `EXTRACTED`

### rationale_for
- Production application runner with health checks and graceful shutdown `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*
