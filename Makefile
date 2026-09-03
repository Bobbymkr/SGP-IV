# Adaptive Traffic Signal Timer - Makefile
# Top 1% team development workflows

.PHONY: help install install-dev install-prod install-ml install-docs install-notebooks
.PHONY: format lint type-check test test-unit test-integration test-performance test-security
.PHONY: pre-commit run-dev run-prod run-demo build docker-build docker-up docker-down
.PHONY: clean clean-pyc clean-dist clean-cache set-city
.PHONY: docs-serve docs-build
.PHONY: check-deps security-audit scan-skills bench-detection train-india-yolo
.PHONY: check-deps security-audit

# Default target
help:
	@echo "Adaptive Traffic Signal Timer - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install        Install core dependencies"
	@echo "  install-dev    Install with development dependencies"
	@echo "  install-prod   Install with production dependencies"
	@echo "  install-ml     Install with ML dependencies"
	@echo "  install-docs   Install with documentation dependencies"
	@echo "  install-notebooks  Install with notebook dependencies"
	@echo "  install-all    Install all optional dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  format         Format code with black and isort"
	@echo "  lint           Run flake8 linter"
	@echo "  type-check     Run mypy type checker"
	@echo "  pre-commit     Run all pre-commit hooks"
	@echo "  check-deps     Check for vulnerable/outdated dependencies"
	@echo "  security-audit Run bandit security audit"
	@echo "  scan-skills    Scan installed agent skills with NVIDIA SkillSpector"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-performance   Run performance tests"
	@echo "  test-security      Run security tests"
	@echo "  test-cov          Run tests with coverage"
	@echo ""
	@echo "Development:"
	@echo "  run-dev        Run FastAPI development server"
	@echo "  run-prod       Run production server with gunicorn"
	@echo "  run-demo       Run Streamlit demo dashboard"
	@echo "  run-tests      Run test suite via script"
	@echo ""
	@echo "City Profile:"
	@echo "  set-city       Set city profile (mumbai, delhi, bangalore, tier2_default)"
	@echo "  list-cities    List available city profiles"
	@echo ""
	@echo "ML/Benchmarks:"
	@echo "  train-india-yolo  Train India YOLO model (docs only - run in Colab)"
	@echo "  bench-detection   Run detection benchmark"
	@echo "  bench-sim         Run simulation benchmark"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-up      Start services with docker-compose"
	@echo "  docker-down    Stop docker-compose services"
	@echo "  docker-logs    View docker-compose logs"
	@echo ""
	@echo "Documentation:"
	@echo "  docs-serve     Serve documentation locally"
	@echo "  docs-build     Build static documentation"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          Remove all generated files"
	@echo "  clean-pyc      Remove Python cache files"
	@echo "  clean-dist     Remove build/dist artifacts"
	@echo "  clean-cache    Remove tool caches"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-prod:
	pip install -e ".[prod]"

install-ml:
	pip install -e ".[ml]"

install-docs:
	pip install -e ".[docs]"

install-notebooks:
	pip install -e ".[notebooks]"

install-all:
	pip install -e ".[dev,prod,ml,docs,notebooks]"

# Code Quality
format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/

type-check:
	mypy src/

pre-commit:
	pre-commit run --all-files

check-deps:
	pip list --outdated
	safety check

security-audit:
	bandit -r src/ -ll --skip B101,B601

# Agent-skills supply-chain scan (NVIDIA SkillSpector, installed outside the
# project venv: uv tool install git+https://github.com/NVIDIA/SkillSpector.git).
# scripts/scan_skills.ps1 enumerates every SKILL.md dir (any depth), batches
# scans around SkillSpector's fail-closed ceilings, gates on non-suppressed
# CRITICAL/HIGH findings and honors .skillspector-baseline.json (accepted
# findings; refresh with -GenerateBaseline after reviewing new findings).
scan-skills:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/scan_skills.ps1 -Paths .agents/skills,.claude/skills

# Testing
test:
	pytest

loop-fast:
	pytest tests/unit tests/integration -q -x --no-header -p no:cacheprovider

verify:
	pytest -q
	flake8 src/adaptive_traffic --count

eval:
	python evals/runner.py

bench-sim:
	python scripts/bench_sim.py

bench-detect:
	python scripts/bench_detect.py

profile-device:
	python scripts/profile_device.py --write

graph-update:
	graphify update .
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/auto-graph.ps1 -Phase graph-update

orca-pipeline:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resume.ps1

orca-status:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resume.ps1 -StatusOnly

vault-sync:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/auto-graph.ps1 -Phase vault-sync

test-unit:
	pytest -m unit -v

test-integration:
	pytest -m integration -v

test-performance:
	pytest -m performance -v

test-security:
	pytest -m security -v

test-cov:
	pytest --cov=src/adaptive_traffic --cov-report=term-missing --cov-report=html

# Development servers
run-dev:
	uvicorn adaptive_traffic.api.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	gunicorn adaptive_traffic.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

run-demo:
	streamlit run src/adaptive_traffic/ui/app.py --server.port 8501

run-tests:
	@echo "DEPRECATED: use 'make verify' or 'make loop-fast'"

# Docker
docker-build:
	docker-compose -f configs/docker/docker-compose.yml build

docker-up:
	docker-compose -f configs/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f configs/docker/docker-compose.yml down

docker-logs:
	docker-compose -f configs/docker/docker-compose.yml logs -f

docker-restart:
	docker-compose -f configs/docker/docker-compose.yml restart

# Documentation
docs-serve:
	mkdocs serve -f docs/mkdocs.yml

docs-build:
	mkdocs build -f docs/mkdocs.yml

# Cleanup
clean: clean-pyc clean-dist clean-cache

clean-pyc:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*$py.class" -delete 2>/dev/null || true

clean-dist:
	rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

clean-cache:
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/ .ruff_cache/ 2>/dev/null || true
	rm -rf .venv/ venv/ 2>/dev/null || true

# CI Simulation
ci: format lint type-check test-cov security-audit
	@echo "All CI checks passed!"

# Quick development cycle
dev: format test-unit
	@echo "Development cycle complete"

# City Profile Commands
set-city:
	@echo "Setting city profile to $(CITY)..."
	@powershell -Command "(Get-Content .env) -replace '^CITY_PROFILE=.*', 'CITY_PROFILE=$(CITY)' | Set-Content .env"
	@echo "City profile set to $(CITY). Run 'make run-dev' to use it."

list-cities:
	@echo "Available city profiles:"
	@python -c "from adaptive_traffic.config.city_profiles import list_city_profiles; print('\n'.join(f'  {c}' for c in list_city_profiles()))"

# ML/Benchmark Commands
train-india-yolo:
	@echo "Training India YOLO model - run in Colab:"
	@echo "  1. Open notebooks/train_india_yolo.ipynb in Google Colab"
	@echo "  2. Mount Google Drive with ITD + IISc datasets"
	@echo "  3. Run all cells"
	@echo "  4. Download model.onnx, model-int8.onnx, metadata.json to models/registry/india-yolov8n/"

bench-detection:
	python scripts/bench_detect.py
