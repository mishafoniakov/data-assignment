"""Конфигурация загрузки логов и аналитических представлений."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestConfig:
    """Настройки пайплайна загрузки логов."""

    default_logs_dir: Path = Path("sample_logs")
    db_path: Path = Path("analytics.duckdb")
    pipeline_log_path: Path = Path("pipeline.log")
    log_file_pattern: str = "*.log"
    event_id_fields: tuple[str, ...] = (
        "ts",
        "task_id",
        "event",
        "stage",
        "model",
        "duration_ms",
        "retries",
        "tokens",
        "error",
    )


EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    event_id BIGINT PRIMARY KEY,
    ts TIMESTAMPTZ,
    level VARCHAR,
    event VARCHAR,
    task_id VARCHAR,
    stage VARCHAR,
    model VARCHAR,
    duration_ms INTEGER,
    retries INTEGER,
    tokens INTEGER,
    error VARCHAR,
    loaded_at TIMESTAMP
)
"""


INGESTION_LOG_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ingestion_log (
    file_path VARCHAR PRIMARY KEY,
    file_hash VARCHAR,
    rows_loaded INTEGER,
    last_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


ANALYTICS_VIEWS_SQL = (
    """
    CREATE OR REPLACE VIEW v_stage_durations AS
    SELECT stage, duration_ms
    FROM events
    WHERE event = 'stage_end' AND duration_ms IS NOT NULL
    """,
    """
    CREATE OR REPLACE VIEW v_stage_pairs AS
    SELECT
        ss.task_id,
        ss.stage,
        ss.ts AS start_time,
        se.ts AS end_time,
        se.duration_ms AS declared_ms,
        ROUND(EXTRACT(EPOCH FROM (se.ts - ss.ts)) * 1000) AS calculated_ms
    FROM events ss
    JOIN events se
        ON ss.task_id = se.task_id
        AND ss.stage = se.stage
        AND ss.event = 'stage_start'
        AND se.event = 'stage_end'
    """,
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


CONFIG = IngestConfig()
