.PHONY: help setup data all run report audit smoke test test-ui lint format web serve screenshots clean

help: ## List targets
	@grep -E '^[a-z0-9-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

setup: ## Install Python (uv) and dashboard (npm) dependencies
	uv sync --locked
	npm --prefix web ci

data: ## Check the committed IBM HR CSV against its SHA-256
	uv run wfintel data

all: data run report audit ## THE one command: employee records to the SQL model, tests, model, recommendations, report and audit

run: ## Run the pipeline into results/<UTC>-<sha7>
	uv run wfintel run

report: ## Render docs/generated/results.md from results/LATEST
	uv run wfintel report

audit: ## Causal-language audit of docs, Power BI notes and dashboard text; fails on any finding
	uv run wfintel audit

smoke: data ## Pipeline on the real data into results/scratch (checks the pipeline, not a result)
	rm -rf results/scratch
	uv run wfintel run --results results/scratch

test: ## Unit, SQL-model, audit and API tests (synthetic data; offline)
	uv run pytest

test-ui: web ## Browser, keyboard and axe accessibility tests (needs Chromium)
	uv run pytest -m ui

lint: ## Ruff, mypy strict, ESLint and TypeScript
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests scripts
	npm --prefix web run lint
	npm --prefix web run typecheck

format: ## Auto-format Python
	uv run ruff format .
	uv run ruff check --fix .

web: ## Build the dashboard into web/dist
	npm --prefix web run build

serve: web ## Serve the dashboard on http://127.0.0.1:8014
	uv run wfintel serve

screenshots: web ## Capture docs/screenshots from the committed result
	uv run python scripts/screenshots.py

clean: ## Remove build output and scratch runs (keeps data/ and results/)
	rm -rf web/dist results/scratch .pytest_cache .mypy_cache .ruff_cache
