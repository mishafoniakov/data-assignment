.PHONY: help generate ingest report test test-ingest test-metrics lint ci clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

generate: ## Generate sample application logs
	@mkdir -p sample_logs
	uv run python generate_logs.py --tasks 200 --out sample_logs/app.log

ingest: ## Load sample logs into DuckDB
	uv run python -m analytics.ingest sample_logs

report: ## Print analytics report from DuckDB
	uv run python -m analytics.report

test: ## Run pytest tests
	$(MAKE) test-ingest
	$(MAKE) test-metrics

test-ingest: ## Run ingest parser/id tests
	uv run pytest tests/test_ingest.py

test-metrics: ## Run analytics metrics tests
	uv run pytest tests/test_metrics.py

lint: ## Run ruff checks
	uv run ruff check analytics/ configs/ models/ tests/ generate_logs.py

ci: ## Run local CI checks
	uv sync
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) generate
	rm -f analytics.duckdb analytics.duckdb.wal
	$(MAKE) ingest
	$(MAKE) ingest
	$(MAKE) report

clean: ## Remove generated logs
	rm -f sample_logs/*.log analytics.duckdb analytics.duckdb.wal pipeline.log