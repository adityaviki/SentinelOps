from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone

from sentinelops.models import Anomaly, Incident, Severity


class IncidentStore:
    """Thread-safe in-memory store for incidents, queryable by the API layer."""

    def __init__(self, max_incidents: int = 200) -> None:
        self._incidents: deque[Incident] = deque(maxlen=max_incidents)
        self._lock = threading.Lock()

    def add(self, incident: Incident) -> None:
        with self._lock:
            self._incidents.appendleft(incident)

    def list_all(self, limit: int = 50, offset: int = 0) -> list[Incident]:
        with self._lock:
            items = list(self._incidents)
        return items[offset : offset + limit]

    def get(self, incident_id: str) -> Incident | None:
        with self._lock:
            for inc in self._incidents:
                if inc.id == incident_id:
                    return inc
        return None

    def count(self) -> int:
        with self._lock:
            return len(self._incidents)

    def get_service_summary(self) -> list[dict]:
        """Return per-service health summary from recent incidents."""
        with self._lock:
            incidents = list(self._incidents)

        service_map: dict[str, dict] = {}
        for inc in incidents:
            for anomaly in inc.anomalies:
                svc = anomaly.service
                if svc not in service_map:
                    service_map[svc] = {
                        "service": svc,
                        "status": "healthy",
                        "last_incident_id": None,
                        "last_incident_at": None,
                        "incident_count": 0,
                        "worst_severity": "P4",
                        "anomalies": [],
                    }
                entry = service_map[svc]
                entry["incident_count"] += 1
                if entry["last_incident_at"] is None or inc.created_at > entry["last_incident_at"]:
                    entry["last_incident_at"] = inc.created_at
                    entry["last_incident_id"] = inc.id

                sev_order = ["P1", "P2", "P3", "P4"]
                if sev_order.index(anomaly.severity.value) < sev_order.index(entry["worst_severity"]):
                    entry["worst_severity"] = anomaly.severity.value

                entry["anomalies"].append({
                    "metric": anomaly.metric.value,
                    "z_score": anomaly.z_score,
                    "current_value": anomaly.current_value,
                    "baseline_mean": anomaly.baseline_mean,
                    "severity": anomaly.severity.value,
                    "timestamp": anomaly.timestamp.isoformat(),
                })

        # Set status based on worst severity
        for entry in service_map.values():
            ws = entry["worst_severity"]
            if ws in ("P1", "P2"):
                entry["status"] = "critical"
            elif ws == "P3":
                entry["status"] = "warning"
            else:
                entry["status"] = "degraded"

        return sorted(service_map.values(), key=lambda x: ["P1", "P2", "P3", "P4"].index(x["worst_severity"]))


# Singleton
incident_store = IncidentStore()
