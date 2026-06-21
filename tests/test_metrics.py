"""Тесты аналитических метрик."""

import duckdb
import pytest

from analytics.report import fetch_error_summary, fetch_model_usage
from configs import (
    ERROR_METRIC_ROWS,
    METRICS_EVENTS_TABLE_SQL,
    METRICS_VIEWS_SQL,
    MODEL_USAGE_ROWS,
)
from models import ErrorMetricTestCase, ExpectedModelUsage, ModelUsageTestCase


def build_metrics_db(rows: tuple[tuple[object, ...], ...]) -> duckdb.DuckDBPyConnection:
    """Создаёт in-memory DuckDB с минимальной схемой для метрик."""
    conn = duckdb.connect(":memory:")
    conn.execute(METRICS_EVENTS_TABLE_SQL)
    conn.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", rows)
    for view_sql in METRICS_VIEWS_SQL:
        conn.execute(view_sql)
    return conn


def test_error_count() -> None:
    """Проверка подсчёта задач с ошибками."""
    case = ErrorMetricTestCase(
        total_tasks=3,
        expected_failed_tasks=1,
        expected_error_rate_pct=100 / 3,
        expected_error_count=1,
    )
    conn = build_metrics_db(ERROR_METRIC_ROWS)

    summary = fetch_error_summary(conn, case.total_tasks)

    assert summary.failed_tasks == case.expected_failed_tasks
    assert summary.error_rate_pct == pytest.approx(case.expected_error_rate_pct)
    assert len(summary.errors) == case.expected_error_count
    assert summary.errors[0].error == "OCRFailed"
    assert summary.errors[0].count == 1
    conn.close()


def test_model_aggregation() -> None:
    """Проверка агрегации по моделям."""
    case = ModelUsageTestCase(
        expected=(
            ExpectedModelUsage(model="gemini", calls=2, total_tokens=300),
            ExpectedModelUsage(model="qwen", calls=1, total_tokens=300),
        )
    )
    conn = build_metrics_db(MODEL_USAGE_ROWS)

    result = sorted(fetch_model_usage(conn), key=lambda metric: metric.model)

    assert len(result) == len(case.expected)
    for actual, expected in zip(result, case.expected, strict=True):
        assert actual.model == expected.model
        assert actual.calls == expected.calls
        assert actual.total_tokens == expected.total_tokens
    conn.close()