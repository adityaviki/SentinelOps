from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from sentinelops.incidents import IncidentManager
from sentinelops.models import Anomaly, MetricType, Severity


class TestIncidentManager:
    def test_creates_incident(self, config, sample_anomaly):
        manager = IncidentManager(config)
        incident = manager.create_incident(
            anomalies=[sample_anomaly],
            correlated_events=[],
            runbooks=[],
            analysis=None,
        )

        assert incident is not None
        assert incident.severity == Severity.P1
        assert "payment-service" in incident.title
        assert incident.id.startswith("INC-")

    def test_dedup_suppresses_duplicate(self, config, sample_anomaly):
        manager = IncidentManager(config)

        first = manager.create_incident(
            anomalies=[sample_anomaly],
            correlated_events=[],
            runbooks=[],
            analysis=None,
        )
        assert first is not None

        second = manager.create_incident(
            anomalies=[sample_anomaly],
            correlated_events=[],
            runbooks=[],
            analysis=None,
        )
        assert second is None  # suppressed by dedup

    def test_uses_highest_severity(self, config, sample_anomaly, sample_anomaly_low):
        manager = IncidentManager(config)
        incident = manager.create_incident(
            anomalies=[sample_anomaly, sample_anomaly_low],
            correlated_events=[],
            runbooks=[],
            analysis=None,
        )

        assert incident is not None
        assert incident.severity == Severity.P1

    def test_empty_anomalies_returns_none(self, config):
        manager = IncidentManager(config)
        incident = manager.create_incident(
            anomalies=[],
            correlated_events=[],
            runbooks=[],
            analysis=None,
        )
        assert incident is None

    def test_cleanup_stale_entries(self, config, sample_anomaly):
        manager = IncidentManager(config)
        manager.create_incident(
            anomalies=[sample_anomaly],
            correlated_events=[],
            runbooks=[],
            analysis=None,
        )

        # Manually age the entry
        for key in manager._recent:
            manager._recent[key] = datetime.now(timezone.utc) - timedelta(hours=2)

        manager.cleanup_stale_entries()
        assert len(manager._recent) == 0
