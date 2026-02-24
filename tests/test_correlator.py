from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sentinelops.correlator import EventCorrelator
from sentinelops.models import Anomaly, CorrelatedEvent, MetricType, Severity


class TestBuildEsqlQuery:
    def test_query_contains_services(self, config):
        correlator = EventCorrelator(config, es=None)  # type: ignore[arg-type]
        anomalies = [
            Anomaly(
                service="svc-a",
                metric=MetricType.ERROR_RATE,
                current_value=100,
                baseline_mean=10,
                baseline_stddev=5,
                z_score=18,
                severity=Severity.P1,
                timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        earliest = min(a.timestamp for a in anomalies)
        query = correlator._build_esql_query(
            affected_services=["svc-a"],
            window_start=datetime(2025, 1, 1, 11, 50, 0, tzinfo=timezone.utc),
            window_end=datetime(2025, 1, 1, 12, 10, 0, tzinfo=timezone.utc),
        )

        assert "svc-a" in query
        assert "error" in query
        assert "warning" in query
        assert "FROM test-logs-*" in query


class TestParseEvents:
    def test_parses_raw_events(self, config):
        correlator = EventCorrelator(config, es=None)  # type: ignore[arg-type]
        raw = [
            {
                "service.name": "svc-b",
                "level": "error",
                "message": "Connection refused",
                "@timestamp": "2025-01-01T12:00:00+00:00",
                "trace.id": "abc123",
                "extra_field": "value",
            }
        ]

        events = correlator._parse_events(raw)
        assert len(events) == 1
        assert events[0].service == "svc-b"
        assert events[0].level == "error"
        assert events[0].trace_id == "abc123"
        assert events[0].metadata == {"extra_field": "value"}

    def test_handles_missing_fields(self, config):
        correlator = EventCorrelator(config, es=None)  # type: ignore[arg-type]
        raw = [{"level": "warning", "message": "slow query"}]

        events = correlator._parse_events(raw)
        assert len(events) == 1
        assert events[0].service == "unknown"
        assert events[0].trace_id is None
