.DEFAULT_GOAL := help

UV ?= uv
HOST ?= 127.0.0.1
PORT ?= 8000

.PHONY: help bootstrap run format format-check lint typecheck test coverage secrets security verify \
	build up down logs smoke demo clean

help: ## Show available project commands
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Create the environment and install locked development dependencies
	$(UV) sync --frozen --group dev

run: ## Run the API directly for local development
	$(UV) run uvicorn ops_pilot.main:app --host $(HOST) --port $(PORT) --reload

format: ## Format Python source and tests
	$(UV) run ruff format .

format-check: ## Verify formatting without changing files
	$(UV) run ruff format --check .

lint: ## Run static lint checks
	$(UV) run ruff check .

typecheck: ## Run strict static type checks
	$(UV) run mypy

test: ## Run the automated test suite
	$(UV) run pytest -q

coverage: ## Run tests with line coverage enforcement
	$(UV) run pytest --cov=ops_pilot --cov-report=term-missing --cov-report=xml --cov-fail-under=85

secrets: ## Scan tracked files against the reviewed secret baseline
	git ls-files -z | xargs -0 $(UV) run detect-secrets-hook --baseline .secrets.baseline

security: ## Run source and dependency security checks
	$(UV) run bandit -c pyproject.toml -r src
	$(UV) run pip-audit

verify: format-check lint typecheck coverage security secrets ## Run the complete local quality gate

build: ## Build the production-like local container image
	docker build --tag ops-pilot:local .

up: ## Build and start OpsPilot through Docker Compose
	docker compose up --build --detach

down: ## Stop and remove the Docker Compose services
	docker compose down --remove-orphans

logs: ## Follow structured container logs
	docker compose logs --follow ops-pilot

smoke: ## Verify a running service through its public health endpoints
	./scripts/smoke.sh http://$(HOST):$(PORT)

demo: ## Exercise supported, unknown, and invalid incident behavior
	./scripts/demo.py http://$(HOST):$(PORT)

clean: ## Remove local generated verification output
	rm -rf .coverage coverage.xml htmlcov .pytest_cache .mypy_cache .ruff_cache
