from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class MetricType(str, Enum):
    ERROR_RATE = "error_rate"
    LATENCY_P99 = "latency_p99"
    LATENCY_P95 = "latency_p95"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"


class Anomaly(BaseModel):
    """A detected anomaly on a single service + metric."""

    service: str
    metric: MetricType
    current_value: float
    baseline_mean: float
    baseline_stddev: float
    z_score: float
    severity: Severity
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def dedup_key(self) -> str:
        raw = f"{self.service}:{self.metric.value}:{self.severity.value}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class CorrelatedEvent(BaseModel):
    """An event from another service related to an anomaly."""

    service: str
    level: str
    message: str
    timestamp: datetime
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Runbook(BaseModel):
    """A historical runbook entry matched to the current incident."""

    title: str
    incident_date: datetime | None = None
    services_affected: list[str] = Field(default_factory=list)
    root_cause: str = ""
    resolution_steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    score: float = 0.0


class AnalysisResult(BaseModel):
    """Output from Claude analysis of an incident."""

    root_cause: str
    confidence: str  # "high", "medium", "low"
    remediation_steps: list[str]
    affected_services: list[str]
    summary: str


class Incident(BaseModel):
    """A fully assembled incident ready for dispatch."""

    id: str = ""
    title: str
    severity: Severity
    anomalies: list[Anomaly]
    correlated_events: list[CorrelatedEvent] = Field(default_factory=list)
    matched_runbooks: list[Runbook] = Field(default_factory=list)
    analysis: AnalysisResult | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dedup_key: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            ts = self.created_at.strftime("%Y%m%d%H%M%S")
            self.id = f"INC-{ts}-{self.dedup_key[:8]}"
