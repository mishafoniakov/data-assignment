"""Тестовые данные для проверки аналитических метрик."""

METRICS_EVENTS_TABLE_SQL = """
CREATE TABLE events (
    task_id VARCHAR,
    event VARCHAR,
    error VARCHAR,
    model VARCHAR,
    tokens INTEGER,
    retries INTEGER
)
"""

METRICS_VIEWS_SQL = (
    """
    CREATE OR REPLACE VIEW v_task_errors AS
    SELECT DISTINCT task_id
    FROM events
    WHERE event IN ('stage_error', 'task_failed')
    """,
    """
    CREATE OR REPLACE VIEW v_error_types AS
    SELECT error, COUNT(*) AS count
    FROM events
    WHERE error IS NOT NULL
    GROUP BY error
    """,
    """
    CREATE OR REPLACE VIEW v_llm_calls AS
    SELECT retries, model, tokens
    FROM events
    WHERE event = 'llm_call'
    """,
)

ERROR_METRIC_ROWS = (
    ("t1", "task_done", None, None, None, None),
    ("t2", "task_done", None, None, None, None),
    ("t3", "stage_error", "OCRFailed", None, None, None),
    ("t3", "task_failed", None, None, None, None),
)

MODEL_USAGE_ROWS = (
    ("t1", "llm_call", None, "gemini", 100, 0),
    ("t1", "llm_call", None, "gemini", 200, 1),
    ("t2", "llm_call", None, "qwen", 300, 0),
)
