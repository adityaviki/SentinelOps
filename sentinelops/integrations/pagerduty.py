from __future__ import annotations

import structlog
import pdpyras

from sentinelops.models import Incident, Severity

logger = structlog.get_logger(__name__)

# Map our severity to PagerDuty urgency
_URGENCY_MAP = {
    Severity.P1: "high",
    Severity.P2: "high",
    Severity.P3: "low",
    Severity.P4: "low",
}


class PagerDutyNotifier:
    """Creates PagerDuty incidents for high-severity events."""

    def __init__(self, api_key: str, service_id: str) -> None:
        self._session = pdpyras.APISession(api_key)
        self._service_id = service_id

    async def notify(self, incident: Incident) -> None:
        """Create a PagerDuty incident. Runs sync client in executor."""
        import asyncio

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._create_incident, incident)
            logger.info("pagerduty.incident.created", incident_id=incident.id)
        except Exception:
            logger.exception("pagerduty.incident.failed", incident_id=incident.id)

    def _create_incident(self, incident: Incident) -> None:
        services = ", ".join({a.service for a in incident.anomalies})
        body_lines = [f"Severity: {incident.severity.value}", f"Services: {services}"]
        if incident.analysis:
            body_lines.append(f"Root cause: {incident.analysis.root_cause}")
            for i, step in enumerate(incident.analysis.remediation_steps, 1):
                body_lines.append(f"  {i}. {step}")

        self._session.rpost(
            "incidents",
            json={
                "incident": {
                    "type": "incident",
                    "title": f"[{incident.severity.value}] {incident.title}",
                    "service": {
                        "id": self._service_id,
                        "type": "service_reference",
                    },
                    "urgency": _URGENCY_MAP.get(incident.severity, "low"),
                    "body": {
                        "type": "incident_body",
                        "details": "\n".join(body_lines),
                    },
                    "incident_key": incident.dedup_key,
                }
            },
        )
