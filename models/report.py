"""Pydantic-модели аналитического отчёта."""

from pydantic import BaseModel, ConfigDict, Field


class ReportModel(BaseModel):
    """Базовая модель отчёта с запретом лишних полей."""

    model_config = ConfigDict(extra="forbid")


class ReportSummary(ReportModel):
    total_events: int = Field(ge=0)
    total_tasks: int = Field(ge=0)


class StageDurationMetric(ReportModel):
    stage: str
    count: int = Field(ge=0)
    avg_ms: int | None = Field(default=None, ge=0)
    p50_ms: int | None = Field(default=None, ge=0)
    p95_ms: int | None = Field(default=None, ge=0)


class ErrorTypeMetric(ReportModel):
    error: str
    count: int = Field(ge=0)


class ErrorSummary(ReportModel):
    failed_tasks: int = Field(ge=0)
    total_tasks: int = Field(ge=0)
    error_rate_pct: float = Field(ge=0)
    errors: list[ErrorTypeMetric]


class LlmRetryMetric(ReportModel):
    retries: int = Field(ge=0)
    calls: int = Field(ge=0)


class LlmRetrySummary(ReportModel):
    total_calls: int = Field(ge=0)
    total_retries: int = Field(ge=0)
    retry_rate_pct: float = Field(ge=0)
    distribution: list[LlmRetryMetric]


class ModelUsageMetric(ReportModel):
    model: str
    calls: int = Field(ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    avg_tokens: int | None = Field(default=None, ge=0)
    avg_retries: float | None = Field(default=None, ge=0)
