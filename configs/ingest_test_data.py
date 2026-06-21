"""Тестовые данные для проверки загрузчика логов."""

PARSER_LOG_LINES = (
    '{"ts": "2026-06-01T09:00:00+03:00", "event": "test", "task_id": "t-1"}',
    "это не JSON",
    '{"ts": "2026-06-01T09:00:01+03:00", "event": "test", "task_id": "t-2"}',
    '{"broken": "json"',
    "",
    '{"ts": "2026-06-01T09:00:02+03:00", "event": "test", "task_id": "t-3"}',
)

EVENT_ID_EVENT = {
    "ts": "2026-01-01T00:00:00+03:00",
    "task_id": "t-1",
    "event": "start",
    "stage": "pre",
}

EVENT_ID_DISTINCT_EVENT = {
    "ts": "2026-01-01T00:00:01+03:00",
    "task_id": "t-1",
    "event": "end",
    "stage": "pre",
}
