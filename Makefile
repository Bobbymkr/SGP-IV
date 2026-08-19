# Adaptive Traffic Signal Timer - Makefile
# Top 1% team development workflows

.PHONY: help install install-dev install-prod install-ml install-docs install-notebooks
.PHONY: format lint type-check test test-unit test-integration test-performance test-security
.PHONY: pre-commit run-dev run-prod run-demo build docker-build docker-up docker-down
.PHONY: clean clean-pyc clean-dist clean-cache
.PHONY: docs-serve docs-build
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

# Testing
test:
	pytest

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
	python tests/run_tests.py

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