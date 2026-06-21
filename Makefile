.PHONY: help run generate ingest report test test-ingest test-metrics lint docker-build docker-compose-config docker-run ci clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Run full local pipeline
	./run.sh local

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

docker-build: ## Build Docker image
	docker build -t data-assignment:latest .

docker-compose-config: ## Validate docker-compose.yml
	docker compose config

docker-run: ## Run full pipeline in Docker Compose
	./run.sh docker

ci: ## Run local CI checks
	uv sync
	$(MAKE) lint
	$(MAKE) test
	./run.sh local

clean: ## Remove generated logs
	rm -f sample_logs/*.log analytics.duckdb analytics.duckdb.wal pipeline.log