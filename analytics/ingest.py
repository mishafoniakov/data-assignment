"""Загрузчик логов в DuckDB.

Распарсивает построчный JSON из лог-директории и загружает события
идемпотентно: повторная загрузка того же файла не дублирует строки.
"""

import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import duckdb
from pydantic import ValidationError

from configs import (
    ANALYTICS_VIEWS_SQL,
    CONFIG,
    EVENTS_TABLE_SQL,
    INGESTION_LOG_TABLE_SQL,
    IngestConfig,
)
from models import LogEvent


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


def generate_event_id(event: LogEvent, config: IngestConfig = CONFIG) -> int:
    """Стабильный бизнес-ключ для идемпотентности."""
    payload = event.event_id_payload(config.event_id_fields)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) & 0x7FFFFFFFFFFFFFFF


def parse_event_line(line: str) -> LogEvent | None:
    """Парсит и валидирует одну строку лога."""
    try:
        payload = json.loads(line)
        return LogEvent.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None


def iter_events(logs_dir: str | Path, config: IngestConfig = CONFIG) -> tuple[list[LogEvent], int, int]:
    """Итерируется по событиям, устойчиво пропуская битые строки."""
    events: list[LogEvent] = []
    bad = 0
    total = 0

    for path in Path(logs_dir).glob(config.log_file_pattern):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1

                event = parse_event_line(line)
                if event is None:
                    bad += 1
                    continue

                events.append(event)

    return events, bad, total


def init_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Создаёт таблицы, если их нет."""
    conn.execute(EVENTS_TABLE_SQL)
    conn.execute(INGESTION_LOG_TABLE_SQL)


def get_file_hash(file_path: Path) -> str:
    """MD5-хеш файла для отслеживания изменений."""
    digest = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_file_incremental(
    conn: duckdb.DuckDBPyConnection,
    file_path: Path,
    config: IngestConfig = CONFIG,
) -> dict[str, int]:
    """Загружает файл инкрементально, пропуская дубликаты."""
    stats = {"new": 0, "skipped": 0, "bad": 0, "total": 0}
    file_key = str(file_path)

    current_hash = get_file_hash(file_path)
    saved = conn.execute(
        "SELECT file_hash, rows_loaded FROM ingestion_log WHERE file_path = ?",
        [file_key],
    ).fetchone()

    if saved and saved[0] == current_hash:
        logger.info("  %s: unchanged, skipping", file_path.name)
        stats["skipped"] = saved[1]
        return stats

    logger.info("  %s: loading...", file_path.name)

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats["total"] += 1

            event = parse_event_line(line)
            if event is None:
                stats["bad"] += 1
                continue

            event_id = generate_event_id(event, config)
            exists = conn.execute(
                "SELECT 1 FROM events WHERE event_id = ?",
                [event_id],
            ).fetchone()
            if exists:
                stats["skipped"] += 1
                continue

            conn.execute(
                """
                INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                event.db_values(event_id, datetime.now()),
            )
            stats["new"] += 1

    conn.execute(
        """
        INSERT OR REPLACE INTO ingestion_log (file_path, file_hash, rows_loaded)
        VALUES (?, ?, ?)
        """,
        [file_key, current_hash, stats["new"] + stats["skipped"]],
    )

    return stats


def create_views(conn: duckdb.DuckDBPyConnection) -> None:
    """Создаёт VIEW для аналитики."""
    for view_sql in ANALYTICS_VIEWS_SQL:
        conn.execute(view_sql)


def main() -> None:
    logs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else CONFIG.default_logs_dir
    logger.info("Reading logs from: %s", logs_dir)

    conn = duckdb.connect(str(CONFIG.db_path))
    init_db(conn)

    total_new = 0
    total_skipped = 0
    total_bad = 0
    total_lines = 0

    for file_path in sorted(logs_dir.glob(CONFIG.log_file_pattern)):
        stats = load_file_incremental(conn, file_path)
        total_new += stats["new"]
        total_skipped += stats["skipped"]
        total_bad += stats["bad"]
        total_lines += stats["total"]

    create_views(conn)

    bad_pct = (total_bad / total_lines * 100) if total_lines > 0 else 0
    total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    logger.info("")
    logger.info("Results:")
    logger.info("  New: %s, Skipped: %s", total_new, total_skipped)
    logger.info("  Corrupted: %s (%.1f%%)", total_bad, bad_pct)
    logger.info("  Total in DB: %s", total_events)

    conn.close()


if __name__ == "__main__":
    main()
