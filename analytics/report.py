"""Аналитические метрики из DuckDB."""

import logging

import duckdb

from configs import (
    CONFIG,
    ERROR_TYPES_SQL,
    FAILED_TASKS_SQL,
    LLM_RETRIES_SQL,
    MODEL_USAGE_SQL,
    REPORT_CONFIG,
    STAGE_DURATIONS_SQL,
    TOTAL_EVENTS_SQL,
    TOTAL_TASKS_SQL,
)
from models import (
    ErrorSummary,
    ErrorTypeMetric,
    LlmRetryMetric,
    LlmRetrySummary,
    ModelUsageMetric,
    ReportSummary,
    StageDurationMetric,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(CONFIG.pipeline_log_path),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def fetch_summary(conn: duckdb.DuckDBPyConnection) -> ReportSummary:
    """Собирает общую статистику отчёта."""
    return ReportSummary(
        total_events=conn.execute(TOTAL_EVENTS_SQL).fetchone()[0],
        total_tasks=conn.execute(TOTAL_TASKS_SQL).fetchone()[0],
    )


def fetch_stage_durations(conn: duckdb.DuckDBPyConnection) -> list[StageDurationMetric]:
    """Собирает метрики длительности этапов."""
    return [
        StageDurationMetric(
            stage=row[0],
            count=row[1],
            avg_ms=row[2],
            p50_ms=row[3],
            p95_ms=row[4],
        )
        for row in conn.execute(STAGE_DURATIONS_SQL).fetchall()
    ]


def fetch_error_summary(
    conn: duckdb.DuckDBPyConnection,
    total_tasks: int,
) -> ErrorSummary:
    """Собирает статистику ошибок."""
    failed_tasks = conn.execute(FAILED_TASKS_SQL).fetchone()[0]
    error_rate_pct = (failed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    errors = [
        ErrorTypeMetric(error=row[0], count=row[1])
        for row in conn.execute(ERROR_TYPES_SQL).fetchall()
    ]
    return ErrorSummary(
        failed_tasks=failed_tasks,
        total_tasks=total_tasks,
        error_rate_pct=error_rate_pct,
        errors=errors,
    )


def fetch_llm_retries(conn: duckdb.DuckDBPyConnection) -> LlmRetrySummary:
    """Собирает статистику ретраев LLM."""
    distribution = [
        LlmRetryMetric(retries=row[0], calls=row[1])
        for row in conn.execute(LLM_RETRIES_SQL).fetchall()
    ]
    total_calls = sum(item.calls for item in distribution)
    total_retries = sum(item.retries * item.calls for item in distribution)
    retry_rate_pct = (total_retries / total_calls * 100) if total_calls > 0 else 0
    return LlmRetrySummary(
        total_calls=total_calls,
        total_retries=total_retries,
        retry_rate_pct=retry_rate_pct,
        distribution=distribution,
    )


def fetch_model_usage(conn: duckdb.DuckDBPyConnection) -> list[ModelUsageMetric]:
    """Собирает статистику использования моделей."""
    return [
        ModelUsageMetric(
            model=row[0],
            calls=row[1],
            total_tokens=row[2],
            avg_tokens=row[3],
            avg_retries=row[4],
        )
        for row in conn.execute(MODEL_USAGE_SQL).fetchall()
    ]


def log_section(title: str) -> None:
    """Печатает заголовок секции отчёта."""
    separator = "=" * REPORT_CONFIG.separator_width
    logger.info("\n%s", separator)
    logger.info(title)
    logger.info(separator)


def log_stage_durations(metrics: list[StageDurationMetric]) -> None:
    log_section("1. STAGE DURATIONS (P50/P95)")
    for metric in metrics:
        logger.info(
            "  %-15s | count=%3s | p50=%5sms | p95=%5sms | avg=%5sms",
            metric.stage,
            metric.count,
            metric.p50_ms,
            metric.p95_ms,
            metric.avg_ms,
        )


def log_error_summary(summary: ErrorSummary) -> None:
    log_section("2. ERROR ANALYSIS")
    logger.info(
        "  Tasks with errors: %s/%s (%.1f%%)",
        summary.failed_tasks,
        summary.total_tasks,
        summary.error_rate_pct,
    )

    total_errors = sum(error.count for error in summary.errors)
    if total_errors == 0:
        return

    for error in summary.errors:
        pct = error.count / total_errors * 100
        logger.info("    - %-20s %2s (%.0f%%)", error.error, error.count, pct)


def log_llm_retries(summary: LlmRetrySummary) -> None:
    log_section("3. LLM RETRIES")
    logger.info("  Total LLM calls: %s", summary.total_calls)
    logger.info("  Total retries: %s", summary.total_retries)
    logger.info("  Retry rate: %.1f%%", summary.retry_rate_pct)
    logger.info("  Distribution:")

    if summary.total_calls == 0:
        return

    for item in summary.distribution:
        pct = item.calls / summary.total_calls * 100
        bar = "█" * int(pct / REPORT_CONFIG.retry_bar_scale)
        logger.info(
            "    %s retries: %4s calls (%5.1f%%) %s",
            item.retries,
            item.calls,
            pct,
            bar,
        )


def log_model_usage(metrics: list[ModelUsageMetric]) -> None:
    log_section("4. MODEL USAGE")
    for metric in metrics:
        logger.info(
            "  %-15s | calls=%4s | tokens=%8s | avg_tok=%4s | avg_retry=%.2f",
            metric.model,
            metric.calls,
            metric.total_tokens,
            metric.avg_tokens,
            metric.avg_retries or 0,
        )


def main() -> None:
    conn = duckdb.connect(str(CONFIG.db_path))

    summary = fetch_summary(conn)
    logger.info("Total events: %s", summary.total_events)
    logger.info("Total tasks: %s", summary.total_tasks)

    log_stage_durations(fetch_stage_durations(conn))
    log_error_summary(fetch_error_summary(conn, summary.total_tasks))
    log_llm_retries(fetch_llm_retries(conn))
    log_model_usage(fetch_model_usage(conn))

    logger.info("\n%s", "=" * REPORT_CONFIG.separator_width)
    logger.info("Done.")

    conn.close()


if __name__ == "__main__":
    main()