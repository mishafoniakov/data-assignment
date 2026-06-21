"""Конфигурация аналитического отчёта."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportConfig:
    """Настройки вывода отчёта."""

    separator_width: int = 60
    retry_bar_scale: int = 2


TOTAL_EVENTS_SQL = "SELECT COUNT(*) FROM events"

TOTAL_TASKS_SQL = """
SELECT COUNT(DISTINCT task_id)
FROM events
WHERE event = 'task_started'
"""

STAGE_DURATIONS_SQL = """
SELECT
    stage,
    COUNT(*) AS count,
    ROUND(AVG(duration_ms)) AS avg_ms,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms)) AS p50_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)) AS p95_ms
FROM v_stage_durations
GROUP BY stage
ORDER BY p95_ms DESC
"""

FAILED_TASKS_SQL = "SELECT COUNT(*) FROM v_task_errors"

ERROR_TYPES_SQL = """
SELECT error, count
FROM v_error_types
ORDER BY count DESC
"""

LLM_RETRIES_SQL = """
SELECT
    retries,
    COUNT(*) AS calls
FROM v_llm_calls
GROUP BY retries
ORDER BY retries
"""

MODEL_USAGE_SQL = """
SELECT
    model,
    COUNT(*) AS calls,
    SUM(tokens) AS total_tokens,
    ROUND(AVG(tokens)) AS avg_tokens,
    ROUND(AVG(retries), 2) AS avg_retries
FROM v_llm_calls
GROUP BY model
ORDER BY calls DESC
"""


REPORT_CONFIG = ReportConfig()
