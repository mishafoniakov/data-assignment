.PHONY: help generate ingest lint ci clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

generate: ## Generate sample application logs
	@mkdir -p sample_logs
	uv run python generate_logs.py --tasks 200 --out sample_logs/app.log

ingest: ## Load sample logs into DuckDB
	uv run python -m analytics.ingest sample_logs

lint: ## Run ruff checks
	uv run ruff check analytics/ generate_logs.py

ci: ## Run local CI checks
	uv sync
	$(MAKE) lint
	$(MAKE) generate
	rm -f analytics.duckdb analytics.duckdb.wal
	$(MAKE) ingest
	$(MAKE) ingest

clean: ## Remove generated logs
	rm -f sample_logs/*.log analytics.duckdb analytics.duckdb.wal pipeline.log