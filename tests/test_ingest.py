"""Тесты парсера логов и генерации event_id."""

from configs import EVENT_ID_DISTINCT_EVENT, EVENT_ID_EVENT, PARSER_LOG_LINES
from analytics.ingest import generate_event_id, iter_events
from models import EventIdTestCase, LogEvent, ParserTestCase


def test_parser_handles_corrupted_lines(tmp_path) -> None:
    """Парсер должен пропускать битые строки и считать статистику."""
    case = ParserTestCase(
        lines=PARSER_LOG_LINES,
        expected_valid=3,
        expected_bad=2,
        expected_total=5,
    )

    log_file = tmp_path / "test.log"
    log_file.write_text(case.content(), encoding="utf-8")

    events, bad, total = iter_events(tmp_path)

    assert len(events) == case.expected_valid
    assert all(isinstance(event, LogEvent) for event in events)
    assert bad == case.expected_bad
    assert total == case.expected_total


def test_event_id_uniqueness() -> None:
    """Разные события должны иметь разные бизнес-ключи."""
    case = EventIdTestCase(
        base_event=LogEvent.model_validate(EVENT_ID_EVENT),
        distinct_event=LogEvent.model_validate(EVENT_ID_DISTINCT_EVENT),
    )

    assert generate_event_id(case.base_event) != generate_event_id(case.distinct_event)


def test_event_id_same() -> None:
    """Одинаковые события — одинаковые ID (идемпотентность)."""
    event = LogEvent.model_validate(EVENT_ID_EVENT)

    assert generate_event_id(event) == generate_event_id(event)
