"""Pydantic-модели тестовых кейсов для ingest."""

from pydantic import BaseModel, ConfigDict, Field

from models.log_event import LogEvent


class ParserTestCase(BaseModel):
    """Тест-кейс для проверки парсинга JSONL-логов."""

    model_config = ConfigDict(extra="forbid")

    lines: tuple[str, ...]
    expected_valid: int = Field(ge=0)
    expected_bad: int = Field(ge=0)
    expected_total: int = Field(ge=0)

    def content(self) -> str:
        """Возвращает содержимое временного log-файла."""
        return "\n".join(self.lines) + "\n"


class EventIdTestCase(BaseModel):
    """Тест-кейс для проверки стабильности event_id."""

    model_config = ConfigDict(extra="forbid")

    base_event: LogEvent
    distinct_event: LogEvent
