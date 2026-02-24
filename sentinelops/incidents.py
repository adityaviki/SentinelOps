from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from sentinelops.config import AppConfig
from sentinelops.models import (
    AnalysisResult,
    Anomaly,
    CorrelatedEvent,
    Incident,
    Runbook,
    Severity,
)

logger = structlog.get_logger(__name__)


class IncidentManager:
    """Creates deduplicated, prioritized incidents from anomalies."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        # dedup_key -> last alert timestamp
        self._recent: dict[str, datetime] = {}

    def create_incident(
        self,
        anomalies: list[Anomaly],
        correlated_events: list[CorrelatedEvent],
        runbooks: list[Runbook],
        analysis: AnalysisResult | None,
    ) -> Incident | None:
        if not anomalies:
            return None

        # Use the highest severity among all anomalies
        severity = min(anomalies, key=lambda a: list(Severity).index(a.severity)).severity

        # Build dedup key from the combined anomaly dedup keys
        combined_dedup = ":".join(sorted({a.dedup_key for a in anomalies}))

        if self._is_duplicate(combined_dedup):
            logger.info("incident.dedup.suppressed", dedup_key=combined_dedup[:16])
            return None

        # Build title
        services = ", ".join(sorted({a.service for a in anomalies}))
        metrics = ", ".join(sorted({a.metric.value for a in anomalies}))
        title = analysis.summary if analysis else f"{metrics} anomaly on {services}"

        incident = Incident(
            title=title,
            severity=severity,
            anomalies=anomalies,
            correlated_events=correlated_events,
            matched_runbooks=runbooks,
            analysis=analysis,
            dedup_key=combined_dedup,
        )

        self._recent[combined_dedup] = incident.created_at
        logger.info(
            "incident.created",
            id=incident.id,
            severity=incident.severity.value,
            title=incident.title,
        )
        return incident

    def _is_duplicate(self, dedup_key: str) -> bool:
        last_seen = self._recent.get(dedup_key)
        if last_seen is None:
            return False
        cooldown = timedelta(minutes=self.config.dedup_cooldown_minutes)
        return datetime.now(timezone.utc) - last_seen < cooldown

    def cleanup_stale_entries(self) -> None:
        """Remove expired dedup entries to prevent memory growth."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=self.config.dedup_cooldown_minutes * 2
        )
        stale = [k for k, v in self._recent.items() if v < cutoff]
        for k in stale:
            del self._recent[k]
