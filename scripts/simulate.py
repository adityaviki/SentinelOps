#!/usr/bin/env python3
"""
Simulate application logs and metrics in Elasticsearch to trigger SentinelOps detections.

Generates:
1. A normal baseline of logs over the past 60 minutes
2. An anomaly spike in the last 5 minutes (error burst + latency spike)
3. Correlated error events across multiple services
4. Seeds the runbook index with historical incident data

Usage:
    python scripts/simulate.py [--es-url http://localhost:9201]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from elasticsearch import Elasticsearch


# ── Configuration ──────────────────────────────────────────────

SERVICES = ["gateway", "payment-service", "order-service", "auth-service", "inventory-service"]
LOG_INDEX = "app-logs-000001"
LOG_ALIAS = "app-logs"
RUNBOOK_INDEX = "incident-runbooks"

NORMAL_ERROR_RATE = 2        # errors per 5-min bucket per service (baseline)
NORMAL_LATENCY_MEAN = 120    # ms
NORMAL_LATENCY_STDDEV = 30   # ms

SPIKE_ERROR_RATE = 60        # errors per 5-min bucket (anomaly)
SPIKE_LATENCY_MEAN = 1800    # ms (anomaly)
SPIKE_LATENCY_STDDEV = 400   # ms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate logs for SentinelOps")
    parser.add_argument("--es-url", default="http://localhost:9201", help="Elasticsearch URL")
    return parser.parse_args()


def create_index(es: Elasticsearch) -> None:
    """Create log index with proper mappings and alias."""
    if es.indices.exists(index=LOG_INDEX):
        es.indices.delete(index=LOG_INDEX)

    es.indices.create(
        index=LOG_INDEX,
        body={
            "aliases": {f"{LOG_ALIAS}-all": {}},
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "service.name": {"type": "keyword"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "duration_ms": {"type": "float"},
                    "trace.id": {"type": "keyword"},
                    "status_code": {"type": "integer"},
                    "endpoint": {"type": "keyword"},
                }
            },
        },
    )
    print(f"  Created index: {LOG_INDEX}")


def create_runbook_index(es: Elasticsearch) -> None:
    """Seed the runbook index from seed.json."""
    if es.indices.exists(index=RUNBOOK_INDEX):
        es.indices.delete(index=RUNBOOK_INDEX)

    es.indices.create(
        index=RUNBOOK_INDEX,
        body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "incident_date": {"type": "date"},
                    "services_affected": {"type": "keyword"},
                    "root_cause": {"type": "text"},
                    "resolution_steps": {"type": "text"},
                    "tags": {"type": "keyword"},
                }
            }
        },
    )

    seed_path = Path(__file__).parent.parent / "runbooks" / "seed.json"
    if seed_path.exists():
        runbooks = json.loads(seed_path.read_text())
        for i, rb in enumerate(runbooks):
            es.index(index=RUNBOOK_INDEX, id=f"rb-{i}", document=rb)
        print(f"  Seeded {len(runbooks)} runbooks")
    else:
        print("  Warning: runbooks/seed.json not found, skipping")


def generate_normal_logs(es: Elasticsearch, minutes: int = 60) -> int:
    """Generate baseline normal traffic for the past N minutes."""
    now = datetime.now(timezone.utc)
    docs: list[dict] = []
    bucket_size = 5  # minutes

    for minutes_ago in range(minutes, 5, -bucket_size):
        bucket_start = now - timedelta(minutes=minutes_ago)

        for service in SERVICES:
            # Normal info/debug logs
            for _ in range(random.randint(40, 80)):
                ts = bucket_start + timedelta(seconds=random.randint(0, bucket_size * 60))
                latency = max(10, random.gauss(NORMAL_LATENCY_MEAN, NORMAL_LATENCY_STDDEV))
                trace_id = uuid.uuid4().hex[:16]
                endpoint = random.choice(["/api/health", "/api/users", "/api/orders", "/api/products"])

                docs.append({
                    "@timestamp": ts.isoformat(),
                    "service.name": service,
                    "level": "info",
                    "message": f"GET {endpoint} completed",
                    "duration_ms": round(latency, 1),
                    "trace.id": trace_id,
                    "status_code": 200,
                    "endpoint": endpoint,
                })

            # Normal error rate (low)
            for _ in range(random.randint(max(0, NORMAL_ERROR_RATE - 1), NORMAL_ERROR_RATE + 1)):
                ts = bucket_start + timedelta(seconds=random.randint(0, bucket_size * 60))
                docs.append({
                    "@timestamp": ts.isoformat(),
                    "service.name": service,
                    "level": "error",
                    "message": random.choice([
                        "Connection timeout after 5000ms",
                        "Failed to parse response body",
                        "Unexpected null in field 'user_id'",
                    ]),
                    "duration_ms": round(random.gauss(NORMAL_LATENCY_MEAN * 2, 100), 1),
                    "trace.id": uuid.uuid4().hex[:16],
                    "status_code": random.choice([500, 502, 503]),
                })

    # Bulk index
    _bulk_index(es, docs)
    return len(docs)


def generate_anomaly_spike(es: Elasticsearch) -> int:
    """Generate an anomaly spike in the last 5 minutes on payment-service + order-service."""
    now = datetime.now(timezone.utc)
    spike_start = now - timedelta(minutes=5)
    docs: list[dict] = []

    # Shared trace IDs to enable correlation
    shared_traces = [uuid.uuid4().hex[:16] for _ in range(15)]

    # ── payment-service: massive error spike + latency ──────────
    for i in range(SPIKE_ERROR_RATE):
        ts = spike_start + timedelta(seconds=random.randint(0, 300))
        trace_id = random.choice(shared_traces) if i < 30 else uuid.uuid4().hex[:16]

        docs.append({
            "@timestamp": ts.isoformat(),
            "service.name": "payment-service",
            "level": "error",
            "message": random.choice([
                "Database connection pool exhausted — all 10 connections in use",
                "Transaction failed: timeout waiting for connection from pool",
                "java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available",
                "Circuit breaker OPEN for payment-db after 10 consecutive failures",
                "Failed to process payment: upstream timeout after 30000ms",
            ]),
            "duration_ms": round(max(500, random.gauss(SPIKE_LATENCY_MEAN, SPIKE_LATENCY_STDDEV)), 1),
            "trace.id": trace_id,
            "status_code": random.choice([500, 503, 504]),
            "endpoint": "/api/payments/process",
        })

    # payment-service: high-latency successful requests
    for _ in range(25):
        ts = spike_start + timedelta(seconds=random.randint(0, 300))
        docs.append({
            "@timestamp": ts.isoformat(),
            "service.name": "payment-service",
            "level": "warning",
            "message": "Slow query detected: SELECT * FROM transactions WHERE ... took 4500ms",
            "duration_ms": round(max(1000, random.gauss(SPIKE_LATENCY_MEAN * 1.5, 500)), 1),
            "trace.id": random.choice(shared_traces),
            "status_code": 200,
            "endpoint": "/api/payments/process",
        })

    # ── order-service: cascading errors from payment-service ────
    for i in range(35):
        ts = spike_start + timedelta(seconds=random.randint(30, 300))  # starts slightly later
        trace_id = random.choice(shared_traces) if i < 20 else uuid.uuid4().hex[:16]

        docs.append({
            "@timestamp": ts.isoformat(),
            "service.name": "order-service",
            "level": "error",
            "message": random.choice([
                "Payment processing failed for order — upstream 503 from payment-service",
                "Timeout waiting for payment-service response after 30s",
                "Order checkout failed: payment-service circuit breaker is OPEN",
                "Retry exhausted (3/3) calling payment-service /api/payments/process",
            ]),
            "duration_ms": round(max(5000, random.gauss(15000, 3000)), 1),
            "trace.id": trace_id,
            "status_code": 503,
            "endpoint": "/api/orders/checkout",
        })

    # ── gateway: elevated 5xx from both services ────────────────
    for _ in range(20):
        ts = spike_start + timedelta(seconds=random.randint(30, 300))
        docs.append({
            "@timestamp": ts.isoformat(),
            "service.name": "gateway",
            "level": "error",
            "message": random.choice([
                "Upstream returned 503: payment-service",
                "Upstream returned 503: order-service",
                "Gateway timeout: request exceeded 30s limit",
            ]),
            "duration_ms": round(random.gauss(30000, 2000), 1),
            "trace.id": random.choice(shared_traces),
            "status_code": random.choice([502, 503, 504]),
            "endpoint": random.choice(["/api/orders/checkout", "/api/payments/process"]),
        })

    # Some normal traffic too (other services stay healthy)
    for service in ["auth-service", "inventory-service"]:
        for _ in range(30):
            ts = spike_start + timedelta(seconds=random.randint(0, 300))
            docs.append({
                "@timestamp": ts.isoformat(),
                "service.name": service,
                "level": "info",
                "message": "Request completed successfully",
                "duration_ms": round(max(10, random.gauss(NORMAL_LATENCY_MEAN, NORMAL_LATENCY_STDDEV)), 1),
                "trace.id": uuid.uuid4().hex[:16],
                "status_code": 200,
            })

    _bulk_index(es, docs)
    return len(docs)


def _bulk_index(es: Elasticsearch, docs: list[dict]) -> None:
    """Bulk index documents into ES."""
    if not docs:
        return

    body: list[dict] = []
    for doc in docs:
        body.append({"index": {"_index": LOG_INDEX}})
        body.append(doc)

    resp = es.bulk(body=body, refresh="wait_for")
    if resp.get("errors"):
        failed = sum(1 for item in resp["items"] if item["index"].get("error"))
        print(f"  Warning: {failed}/{len(docs)} documents failed to index")


def main() -> None:
    args = parse_args()
    es = Elasticsearch(args.es_url)

    # Verify connection
    info = es.info()
    print(f"Connected to Elasticsearch {info['version']['number']}")

    print("\n[1/4] Creating log index...")
    create_index(es)

    print("[2/4] Seeding runbooks...")
    create_runbook_index(es)

    print("[3/4] Generating 60 min of normal baseline traffic...")
    normal_count = generate_normal_logs(es, minutes=60)
    print(f"  Indexed {normal_count} normal log entries")

    print("[4/4] Injecting anomaly spike (last 5 minutes)...")
    spike_count = generate_anomaly_spike(es)
    print(f"  Indexed {spike_count} anomaly entries")

    print(f"\nDone! Total: {normal_count + spike_count} documents")
    print("\nThe simulated incident:")
    print("  - payment-service: connection pool exhaustion → error spike + latency surge")
    print("  - order-service: cascading failures from payment-service timeouts")
    print("  - gateway: elevated 5xx from both downstream services")
    print("\nSentinelOps should detect this on its next polling cycle (within 30s).")
    print("Watch logs: docker compose logs -f sentinelops")


if __name__ == "__main__":
    main()
