from __future__ import annotations

from datetime import datetime, timezone

import pytest

from sentinelops.config import AppConfig
from sentinelops.models import Anomaly, MetricType, Severity


@pytest.fixture
def config(tmp_path):
    """Create a minimal config for testing."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """\
polling:
  interval_seconds: 10
  lookback_minutes: 5
detection:
  thresholds:
    p1: 5.0
    p2: 3.5
    p3: 2.5
    p4: 2.0
  baseline_window_minutes: 60
  min_data_points: 5
correlation:
  window_minutes: 10
  max_events: 50
incidents:
  dedup_cooldown_minutes: 30
  pagerduty_severities: ["P1", "P2"]
elasticsearch:
  log_index: "test-logs-*"
  metrics_index: "test-metrics-*"
  runbook_index: "test-runbooks"
analyzer:
  model: "claude-sonnet-4-6"
  max_tokens: 512
"""
    )
    return AppConfig(str(config_file))


@pytest.fixture
def sample_anomaly():
    return Anomaly(
        service="payment-service",
        metric=MetricType.ERROR_RATE,
        current_value=150.0,
        baseline_mean=20.0,
        baseline_stddev=5.0,
        z_score=26.0,
        severity=Severity.P1,
        timestamp=datetime.now(timezone.utc),
        details={"baseline_points": 12},
    )


@pytest.fixture
def sample_anomaly_low():
    return Anomaly(
        service="auth-service",
        metric=MetricType.LATENCY_P99,
        current_value=500.0,
        baseline_mean=200.0,
        baseline_stddev=50.0,
        z_score=6.0,
        severity=Severity.P1,
        timestamp=datetime.now(timezone.utc),
    )
