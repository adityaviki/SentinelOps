from __future__ import annotations

from datetime import datetime

import structlog

from sentinelops.config import AppConfig
from sentinelops.integrations.elasticsearch import ElasticsearchClient
from sentinelops.models import Anomaly, Runbook

logger = structlog.get_logger(__name__)


class RunbookSearch:
    """Searches Elasticsearch for historical runbooks matching current anomalies."""

    def __init__(self, config: AppConfig, es: ElasticsearchClient) -> None:
        self.config = config
        self.es = es

    async def find_matching(self, anomalies: list[Anomaly]) -> list[Runbook]:
        if not anomalies:
            return []

        services = list({a.service for a in anomalies})
        keywords = list({a.metric.value for a in anomalies})

        logger.info("runbooks.search", services=services, keywords=keywords)

        try:
            hits = await self.es.search_runbooks(
                index=self.config.runbook_index,
                services=services,
                error_keywords=keywords,
                max_results=5,
            )
        except Exception:
            logger.exception("runbooks.search.failed")
            return []

        runbooks: list[Runbook] = []
        for hit in hits:
            incident_date = None
            if hit.get("incident_date"):
                try:
                    incident_date = datetime.fromisoformat(hit["incident_date"])
                except (ValueError, TypeError):
                    pass

            runbooks.append(
                Runbook(
                    title=hit.get("title", "Untitled"),
                    incident_date=incident_date,
                    services_affected=hit.get("services_affected", []),
                    root_cause=hit.get("root_cause", ""),
                    resolution_steps=hit.get("resolution_steps", []),
                    tags=hit.get("tags", []),
                    score=hit.get("_score", 0),
                )
            )

        logger.info("runbooks.matched", count=len(runbooks))
        return runbooks
