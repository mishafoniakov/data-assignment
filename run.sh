#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-local}"
TASKS="${TASKS:-200}"
LOGS_DIR="${LOGS_DIR:-sample_logs}"
LOG_FILE="${LOG_FILE:-${LOGS_DIR}/app.log}"
DB_PATH="${DUCKDB_PATH:-analytics.duckdb}"

run_local() {
  echo "==> Sync dependencies"
  uv sync

  echo "==> Generate ${TASKS} synthetic log tasks"
  mkdir -p "${LOGS_DIR}"
  uv run python generate_logs.py --tasks "${TASKS}" --out "${LOG_FILE}"

  echo "==> Reset local DuckDB database"
  rm -f "${DB_PATH}" "${DB_PATH}.wal"

  echo "==> Ingest logs"
  uv run python -m analytics.ingest "${LOGS_DIR}"

  echo "==> Re-run ingest to verify idempotency"
  uv run python -m analytics.ingest "${LOGS_DIR}"

  echo "==> Generate analytics report"
  uv run python -m analytics.report
}

run_docker() {
  echo "==> Validate Docker Compose"
  docker compose config

  echo "==> Build Docker image"
  docker build -t data-assignment:latest .

  echo "==> Run full Docker pipeline"
  docker compose --profile full run --rm all
}

case "${MODE}" in
  local)
    run_local
    ;;
  docker)
    run_docker
    ;;
  *)
    echo "Usage: ./run.sh [local|docker]" >&2
    exit 2
    ;;
esac
