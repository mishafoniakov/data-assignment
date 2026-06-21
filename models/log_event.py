"""Pydantic-модель события из JSONL-логов."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LogEvent(BaseModel):
    """Нормализованное событие из построчного JSON-лога."""

    model_config = ConfigDict(extra="ignore")

    ts: datetime
    event: str
    level: str | None = None
    task_id: str | None = None
    stage: str | None = None
    model: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    retries: int | None = Field(default=None, ge=0)
    tokens: int | None = Field(default=None, ge=0)
    error: str | None = None

    def event_id_payload(self, fields: tuple[str, ...]) -> str:
        """Возвращает стабильное представление бизнес-ключа."""
        return "|".join(str(getattr(self, field, "") or "") for field in fields)

    def db_values(self, event_id: int, loaded_at: datetime) -> list[object]:
        """Возвращает значения в порядке колонок таблицы events."""
        return [
            event_id,
            self.ts,
            self.level,
            self.event,
            self.task_id,
            self.stage,
            self.model,
            self.duration_ms,
            self.retries,
            self.tokens,
            self.error,
            loaded_at,
        ]
