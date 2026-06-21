"""Pydantic-модели тест-кейсов для аналитических метрик."""

from pydantic import BaseModel, ConfigDict, Field


class MetricsTestCase(BaseModel):
    """Базовый тест-кейс аналитических метрик."""

    model_config = ConfigDict(extra="forbid")


class ErrorMetricTestCase(MetricsTestCase):
    total_tasks: int = Field(ge=0)
    expected_failed_tasks: int = Field(ge=0)
    expected_error_rate_pct: float = Field(ge=0)
    expected_error_count: int = Field(ge=0)


class ExpectedModelUsage(MetricsTestCase):
    model: str
    calls: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ModelUsageTestCase(MetricsTestCase):
    expected: tuple[ExpectedModelUsage, ...]
