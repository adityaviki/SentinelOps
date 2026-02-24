from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from sentinelops.config import AppConfig
from sentinelops.integrations.elasticsearch import ElasticsearchClient
from sentinelops.models import Anomaly, MetricType, Severity

logger = structlog.get_logger(__name__)

# Metrics to monitor: (metric_type, ES aggregation field, bucket_field)
METRIC_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": MetricType.ERROR_RATE,
        "query": {
            "filter": {"term": {"level": "error"}},
            "description": "error log count per service",
        },
    },
    {
        "type": MetricType.LATENCY_P99,
        "query": {
            "field": "duration_ms",
            "percentile": 99,
            "description": "p99 latency per service",
        },
    },
]


class AnomalyDetector:
    """Detects anomalies in Elasticsearch metrics using z-score analysis."""

    def __init__(self, config: AppConfig, es: ElasticsearchClient) -> None:
        self.config = config
        self.es = es

    async def detect(self) -> list[Anomaly]:
        """Run all detection checks and return any anomalies found."""
        anomalies: list[Anomaly] = []

        now = datetime.now(timezone.utc)
        lookback = now - timedelta(minutes=self.config.lookback_minutes)
        baseline_start = now - timedelta(minutes=self.config.baseline_window_minutes)

        services = await self.es.get_active_services(
            index=self.config.log_index,
            since=lookback,
        )

        logger.info("detection.cycle.start", services=len(services))

        for service in services:
            for metric_def in METRIC_DEFINITIONS:
                anomaly = await self._check_metric(
                    service=service,
                    metric_def=metric_def,
                    current_start=lookback,
                    current_end=now,
                    baseline_start=baseline_start,
                    baseline_end=lookback,
                )
                if anomaly:
                    anomalies.append(anomaly)

        logger.info("detection.cycle.complete", anomalies=len(anomalies))
        return anomalies

    async def _check_metric(
        self,
        service: str,
        metric_def: dict[str, Any],
        current_start: datetime,
        current_end: datetime,
        baseline_start: datetime,
        baseline_end: datetime,
    ) -> Anomaly | None:
        metric_type: MetricType = metric_def["type"]

        if metric_type == MetricType.ERROR_RATE:
            current_val = await self.es.get_error_count(
                index=self.config.log_index,
                service=service,
                start=current_start,
                end=current_end,
            )
            baseline_values = await self.es.get_error_count_series(
                index=self.config.log_index,
                service=service,
                start=baseline_start,
                end=baseline_end,
                bucket_minutes=self.config.lookback_minutes,
            )
        elif metric_type in (MetricType.LATENCY_P99, MetricType.LATENCY_P95):
            percentile = metric_def["query"].get("percentile", 99)
            current_val = await self.es.get_latency_percentile(
                index=self.config.log_index,
                service=service,
                start=current_start,
                end=current_end,
                percentile=percentile,
            )
            baseline_values = await self.es.get_latency_percentile_series(
                index=self.config.log_index,
                service=service,
                start=baseline_start,
                end=baseline_end,
                percentile=percentile,
                bucket_minutes=self.config.lookback_minutes,
            )
        else:
            return None

        if len(baseline_values) < self.config.min_data_points:
            logger.debug(
                "detection.insufficient_data",
                service=service,
                metric=metric_type.value,
                data_points=len(baseline_values),
            )
            return None

        mean, stddev = _compute_stats(baseline_values)
        if stddev == 0:
            return None

        z_score = (current_val - mean) / stddev
        if z_score < self.config.thresholds["p4"]:
            return None

        severity = _z_score_to_severity(z_score, self.config.thresholds)

        anomaly = Anomaly(
            service=service,
            metric=metric_type,
            current_value=current_val,
            baseline_mean=round(mean, 2),
            baseline_stddev=round(stddev, 2),
            z_score=round(z_score, 2),
            severity=severity,
            timestamp=current_end,
            details={
                "baseline_points": len(baseline_values),
                "lookback_minutes": self.config.lookback_minutes,
            },
        )
        logger.warning(
            "anomaly.detected",
            service=service,
            metric=metric_type.value,
            z_score=round(z_score, 2),
            severity=severity.value,
        )
        return anomaly


def _compute_stats(values: list[float]) -> tuple[float, float]:
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return mean, math.sqrt(variance)


def _z_score_to_severity(z_score: float, thresholds: dict[str, float]) -> Severity:
    if z_score >= thresholds["p1"]:
        return Severity.P1
    if z_score >= thresholds["p2"]:
        return Severity.P2
    if z_score >= thresholds["p3"]:
        return Severity.P3
    return Severity.P4
