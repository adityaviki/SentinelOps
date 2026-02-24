from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from sentinelops.config import AppConfig
from sentinelops.integrations.elasticsearch import ElasticsearchClient
from sentinelops.models import Anomaly, CorrelatedEvent

logger = structlog.get_logger(__name__)


class EventCorrelator:
    """Correlates anomalies with related events across services using ES|QL."""

    def __init__(self, config: AppConfig, es: ElasticsearchClient) -> None:
        self.config = config
        self.es = es

    async def correlate(self, anomalies: list[Anomaly]) -> list[CorrelatedEvent]:
        """Find events across services related to the detected anomalies."""
        if not anomalies:
            return []

        # Determine time window around the earliest anomaly
        earliest = min(a.timestamp for a in anomalies)
        window_start = earliest - timedelta(minutes=self.config.correlation_window_minutes)
        window_end = earliest + timedelta(minutes=self.config.correlation_window_minutes)

        affected_services = list({a.service for a in anomalies})

        logger.info(
            "correlation.start",
            affected_services=affected_services,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
        )

        # ES|QL query to find related error/warning events across all services
        esql_query = self._build_esql_query(
            affected_services=affected_services,
            window_start=window_start,
            window_end=window_end,
        )

        raw_events = await self.es.esql_query(esql_query)
        events = self._parse_events(raw_events)

        logger.info("correlation.complete", events=len(events))
        return events[: self.config.max_correlated_events]

    def _build_esql_query(
        self,
        affected_services: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> str:
        services_list = ", ".join(f'"{s}"' for s in affected_services)

        return f"""\
FROM {self.config.log_index}
| WHERE @timestamp >= "{window_start.isoformat()}"
    AND @timestamp <= "{window_end.isoformat()}"
    AND (level == "error" OR level == "warning")
| SORT @timestamp DESC
| LIMIT {self.config.max_correlated_events}"""

    def _parse_events(self, raw_events: list[dict]) -> list[CorrelatedEvent]:
        events: list[CorrelatedEvent] = []
        for row in raw_events:
            events.append(
                CorrelatedEvent(
                    service=row.get("service.name", row.get("service", "unknown")),
                    level=row.get("level", "unknown"),
                    message=row.get("message", ""),
                    timestamp=datetime.fromisoformat(
                        row.get("@timestamp", datetime.now(timezone.utc).isoformat())
                    ),
                    trace_id=row.get("trace.id"),
                    metadata={
                        k: v
                        for k, v in row.items()
                        if k not in {"service.name", "level", "message", "@timestamp", "trace.id"}
                    },
                )
            )
        return events
