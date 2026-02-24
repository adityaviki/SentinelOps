from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from elasticsearch import AsyncElasticsearch

logger = structlog.get_logger(__name__)


class ElasticsearchClient:
    """Async Elasticsearch client wrapper for logs, metrics, and ES|QL queries."""

    def __init__(self, url: str, api_key: str = "") -> None:
        kwargs: dict[str, Any] = {"hosts": [url]}
        if api_key:
            kwargs["api_key"] = api_key
        else:
            # Local dev: disable SSL verification for self-signed certs
            kwargs["verify_certs"] = False
        self._client = AsyncElasticsearch(**kwargs)

    async def close(self) -> None:
        await self._client.close()

    # ── Service discovery ──────────────────────────────────────────

    async def get_active_services(self, index: str, since: datetime) -> list[str]:
        """Return distinct service names with log activity since the given time."""
        resp = await self._client.search(
            index=index,
            size=0,
            query={"range": {"@timestamp": {"gte": since.isoformat()}}},
            aggs={"services": {"terms": {"field": "service.name", "size": 200}}},
        )
        buckets = resp.get("aggregations", {}).get("services", {}).get("buckets", [])
        return [b["key"] for b in buckets]

    # ── Error rate metrics ─────────────────────────────────────────

    async def get_error_count(
        self, index: str, service: str, start: datetime, end: datetime
    ) -> float:
        resp = await self._client.count(
            index=index,
            query={
                "bool": {
                    "filter": [
                        {"term": {"service.name": service}},
                        {"term": {"level": "error"}},
                        {"range": {"@timestamp": {"gte": start.isoformat(), "lte": end.isoformat()}}},
                    ]
                }
            },
        )
        return float(resp["count"])

    async def get_error_count_series(
        self,
        index: str,
        service: str,
        start: datetime,
        end: datetime,
        bucket_minutes: int = 5,
    ) -> list[float]:
        """Return a time-series of error counts in fixed buckets."""
        resp = await self._client.search(
            index=index,
            size=0,
            query={
                "bool": {
                    "filter": [
                        {"term": {"service.name": service}},
                        {"term": {"level": "error"}},
                        {"range": {"@timestamp": {"gte": start.isoformat(), "lte": end.isoformat()}}},
                    ]
                }
            },
            aggs={
                "over_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "fixed_interval": f"{bucket_minutes}m",
                    }
                }
            },
        )
        buckets = resp.get("aggregations", {}).get("over_time", {}).get("buckets", [])
        return [float(b["doc_count"]) for b in buckets]

    # ── Latency metrics ────────────────────────────────────────────

    async def get_latency_percentile(
        self,
        index: str,
        service: str,
        start: datetime,
        end: datetime,
        percentile: int = 99,
    ) -> float:
        resp = await self._client.search(
            index=index,
            size=0,
            query={
                "bool": {
                    "filter": [
                        {"term": {"service.name": service}},
                        {"range": {"@timestamp": {"gte": start.isoformat(), "lte": end.isoformat()}}},
                        {"exists": {"field": "duration_ms"}},
                    ]
                }
            },
            aggs={
                "latency": {
                    "percentiles": {
                        "field": "duration_ms",
                        "percents": [percentile],
                    }
                }
            },
        )
        values = resp.get("aggregations", {}).get("latency", {}).get("values", {})
        return float(values.get(str(float(percentile)), 0))

    async def get_latency_percentile_series(
        self,
        index: str,
        service: str,
        start: datetime,
        end: datetime,
        percentile: int = 99,
        bucket_minutes: int = 5,
    ) -> list[float]:
        resp = await self._client.search(
            index=index,
            size=0,
            query={
                "bool": {
                    "filter": [
                        {"term": {"service.name": service}},
                        {"range": {"@timestamp": {"gte": start.isoformat(), "lte": end.isoformat()}}},
                        {"exists": {"field": "duration_ms"}},
                    ]
                }
            },
            aggs={
                "over_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "fixed_interval": f"{bucket_minutes}m",
                    },
                    "aggs": {
                        "latency": {
                            "percentiles": {
                                "field": "duration_ms",
                                "percents": [percentile],
                            }
                        }
                    },
                }
            },
        )
        buckets = resp.get("aggregations", {}).get("over_time", {}).get("buckets", [])
        values: list[float] = []
        for b in buckets:
            val = b.get("latency", {}).get("values", {}).get(str(float(percentile)), 0)
            values.append(float(val))
        return values

    # ── ES|QL ──────────────────────────────────────────────────────

    async def esql_query(self, query: str) -> list[dict[str, Any]]:
        """Execute an ES|QL query and return rows as dicts."""
        logger.debug("esql.query", query=query)
        resp = await self._client.esql.query(query=query, format="json")
        columns = [col["name"] for col in resp.get("columns", [])]
        rows: list[dict[str, Any]] = []
        for values in resp.get("values", []):
            rows.append(dict(zip(columns, values)))
        return rows

    # ── Runbook search ─────────────────────────────────────────────

    async def search_runbooks(
        self,
        index: str,
        services: list[str],
        error_keywords: list[str],
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the runbook index for entries matching services or keywords."""
        should_clauses: list[dict] = []

        if services:
            should_clauses.append({"terms": {"services_affected": services}})
        for kw in error_keywords[:10]:
            should_clauses.append({"match": {"root_cause": kw}})
            should_clauses.append({"match": {"tags": kw}})

        if not should_clauses:
            return []

        resp = await self._client.search(
            index=index,
            size=max_results,
            query={"bool": {"should": should_clauses, "minimum_should_match": 1}},
            sort=[{"_score": "desc"}],
        )
        hits = resp.get("hits", {}).get("hits", [])
        return [
            {**hit["_source"], "_score": hit.get("_score", 0)}
            for hit in hits
        ]

    # ── Index management (for seeding) ─────────────────────────────

    async def index_document(self, index: str, doc: dict[str, Any], doc_id: str | None = None) -> None:
        await self._client.index(index=index, id=doc_id, document=doc)

    async def ensure_index(self, index: str, mappings: dict[str, Any] | None = None) -> None:
        exists = await self._client.indices.exists(index=index)
        if not exists:
            body: dict[str, Any] = {}
            if mappings:
                body["mappings"] = mappings
            await self._client.indices.create(index=index, body=body)
