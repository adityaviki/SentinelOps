# SentinelOps

An AI-powered Incident Response Triage Agent that monitors application logs and metrics in Elasticsearch, detects anomalies, correlates events across services, and creates prioritized incidents with intelligent remediation suggestions.

## How It Works

SentinelOps runs as a long-lived async Python service that executes a continuous detection loop:

```
[Elasticsearch Logs/Metrics]
         |
         v
   +--------------+
   |   Detector    |  Poll ES every 30s, compute z-scores on
   |               |  error rates & p99 latency per service
   +------+-------+
          |  Anomalies detected
          v
   +--------------+
   |  Correlator   |  ES|QL queries to find related errors
   |               |  across services in the same time window
   +------+-------+
          |  Correlated event group
          v
   +--------------+
   |   Runbooks    |  Search ES for matching historical
   |               |  incident runbooks by service & pattern
   +------+-------+
          |  Matching runbooks
          v
   +--------------+
   |   Analyzer    |  Send full context to Claude API -
   |   (Claude)    |  get root cause + remediation steps
   +------+-------+
          |  Analysis result
          v
   +--------------+
   |   Incidents   |  Dedup, assign severity (P1-P4),
   |               |  create incident record
   +------+-------+
          |
     +----+----+
     |         |
     v         v
  [Slack]  [PagerDuty]
  Block Kit  P1/P2 only
  message
```

## Architecture

### Anomaly Detection (`sentinelops/detector.py`)

Uses **z-score analysis** over a rolling baseline window to detect statistical outliers. For each active service, the detector computes:

- **Error rate**: Count of `level: error` logs in the current window vs. the historical baseline
- **p99 latency**: 99th percentile of `duration_ms` in the current window vs. baseline

A z-score represents how many standard deviations the current value is from the baseline mean. Severity is assigned based on configurable thresholds:

| Severity | Z-score threshold | PagerDuty |
|----------|-------------------|-----------|
| P1       | >= 5.0            | Yes       |
| P2       | >= 3.5            | Yes       |
| P3       | >= 2.5            | No        |
| P4       | >= 2.0            | No        |

Detection requires a minimum number of baseline data points (default: 10) to avoid false positives on services with sparse traffic.

### Event Correlation (`sentinelops/correlator.py`)

When anomalies are detected, the correlator runs an **ES|QL query** to find related error and warning events across all services within a configurable time window around the anomaly. This surfaces cascading failures, e.g., a database connection pool exhaustion in `payment-service` causing timeouts in `order-service` and 5xx errors at the `gateway`.

### Runbook Search (`sentinelops/runbooks.py`)

Searches an Elasticsearch index of historical incident runbooks for entries matching the affected services and metric types. Matched runbooks provide the AI analyzer with historical context — what went wrong before and how it was fixed.

### AI Analysis (`sentinelops/analyzer.py`)

Sends the full incident context (anomalies, correlated events, matching runbooks) to the **Claude API** with a structured prompt. Claude returns:

- **Root cause** identification
- **Confidence** level (high/medium/low)
- **Affected services** list
- **Prioritized remediation steps**
- **Summary** suitable as an incident title

### Incident Management (`sentinelops/incidents.py`)

Creates deduplicated incidents using a **hash-based dedup key** derived from (service, metric, severity). A configurable cooldown window (default: 30 minutes) prevents alert storms — if the same anomaly pattern fires again within the cooldown, it is suppressed.

### Notifications

- **Slack** (`sentinelops/integrations/slack.py`): Sends rich Block Kit messages with anomaly details, AI analysis, and matched runbooks
- **PagerDuty** (`sentinelops/integrations/pagerduty.py`): Creates incidents for P1/P2 severity only, with dedup keys to prevent duplicate pages

## Project Structure

```
SentinelOps/
├── pyproject.toml                  # Package definition & dependencies
├── config.yaml                     # Detection thresholds, polling config, ES indices
├── .env.example                    # Required API keys template
├── Dockerfile
├── docker-compose.yml              # ES + Kibana + SentinelOps
├── sentinelops/
│   ├── main.py                     # Async polling loop & signal handling
│   ├── config.py                   # YAML + env var configuration
│   ├── models.py                   # Pydantic models (Anomaly, Incident, etc.)
│   ├── detector.py                 # Z-score anomaly detection
│   ├── correlator.py               # ES|QL cross-service correlation
│   ├── analyzer.py                 # Claude API integration
│   ├── runbooks.py                 # Historical runbook search
│   ├── incidents.py                # Incident creation & dedup
│   ├── integrations/
│   │   ├── elasticsearch.py        # Async ES client wrapper
│   │   ├── slack.py                # Slack Block Kit notifications
│   │   └── pagerduty.py            # PagerDuty event creation
│   └── utils/
│       └── logging.py              # Structured logging (structlog)
├── runbooks/
│   └── seed.json                   # 5 sample historical runbooks
├── scripts/
│   └── simulate.py                 # Inject simulated logs & anomalies
└── tests/
    ├── conftest.py                 # Shared fixtures
    ├── test_detector.py            # Z-score & severity tests
    ├── test_correlator.py          # ES|QL query & event parsing tests
    └── test_incidents.py           # Incident creation & dedup tests
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose

### 1. Configure

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
ANTHROPIC_API_KEY=sk-ant-...        # Required for AI analysis
SLACK_BOT_TOKEN=xoxb-...            # Optional - for Slack notifications
SLACK_CHANNEL_ID=C0123456789        # Optional - Slack channel to post to
PAGERDUTY_API_KEY=...               # Optional - for PagerDuty escalation
PAGERDUTY_SERVICE_ID=...            # Optional - PagerDuty service ID
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

This starts:
- **Elasticsearch** on `localhost:9201`
- **Kibana** on `localhost:5601`
- **SentinelOps** polling every 30 seconds

### 3. Inject Simulated Data

In a separate terminal, inject sample logs with an anomaly spike:

```bash
pip install elasticsearch
python scripts/simulate.py --es-url http://localhost:9201
```

This creates:
- 60 minutes of normal baseline traffic across 5 services
- A 5-minute anomaly spike: connection pool exhaustion in `payment-service` causing cascading failures in `order-service` and `gateway`
- 5 historical runbooks seeded into Elasticsearch

### 4. Watch the Detection

```bash
docker compose logs -f sentinelops
```

Within 30 seconds you'll see the full pipeline fire:

```
anomaly.detected   service=payment-service  metric=error_rate   z_score=14.2  severity=P1
anomaly.detected   service=order-service    metric=error_rate   z_score=22.4  severity=P1
anomaly.detected   service=gateway          metric=error_rate   z_score=25.4  severity=P1
correlation.complete  events=50
runbooks.matched      count=2
analyzer.complete     confidence=high
incident.created      id=INC-20260220192027  severity=P1
```

### Run Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
sentinelops                      # uses config.yaml in current directory
sentinelops /path/to/config.yaml # custom config path
```

## Configuration

All runtime configuration lives in `config.yaml`:

```yaml
polling:
  interval_seconds: 30       # How often to poll ES
  lookback_minutes: 5        # Current window to check for anomalies

detection:
  thresholds:                # Z-score thresholds per severity
    p1: 5.0
    p2: 3.5
    p3: 2.5
    p4: 2.0
  baseline_window_minutes: 60  # Historical window for baseline stats
  min_data_points: 10          # Min data points for reliable baseline

correlation:
  window_minutes: 10         # Time window around anomaly for related events
  max_events: 50             # Max correlated events to include

incidents:
  dedup_cooldown_minutes: 30 # Suppress duplicate alerts within this window
  pagerduty_severities:      # Only page for these severities
    - P1
    - P2

elasticsearch:
  log_index: "app-logs-all"
  metrics_index: "app-metrics-*"
  runbook_index: "incident-runbooks"

analyzer:
  model: "claude-sonnet-4-6"
  max_tokens: 1024
```

Secrets (API keys, tokens) are loaded from environment variables or `.env`.

## Elasticsearch Index Schema

SentinelOps expects log documents with these fields:

| Field          | Type    | Description                        |
|----------------|---------|------------------------------------|
| `@timestamp`   | date    | Event timestamp                    |
| `service.name` | keyword | Service that produced the log      |
| `level`        | keyword | Log level (`info`, `error`, etc.)  |
| `message`      | text    | Log message                        |
| `duration_ms`  | float   | Request duration in milliseconds   |
| `trace.id`     | keyword | Distributed trace ID               |
| `status_code`  | integer | HTTP status code                   |

Runbook documents in the `incident-runbooks` index:

| Field               | Type    | Description                          |
|---------------------|---------|--------------------------------------|
| `title`             | text    | Incident title                       |
| `incident_date`     | date    | When the incident occurred           |
| `services_affected` | keyword | List of affected service names       |
| `root_cause`        | text    | What caused the incident             |
| `resolution_steps`  | text    | Steps taken to resolve               |
| `tags`              | keyword | Searchable tags (e.g., `error_rate`) |

## Testing

```bash
source .venv/bin/activate
pytest tests/ -v
```

```
tests/test_detector.py      - Z-score computation & severity mapping
tests/test_correlator.py     - ES|QL query building & event parsing
tests/test_incidents.py      - Incident creation, dedup & cleanup
```

## Tech Stack

| Component       | Technology                     |
|-----------------|--------------------------------|
| Runtime         | Python 3.11+ / asyncio         |
| Data source     | Elasticsearch 8.x              |
| AI analysis     | Claude API (Anthropic)         |
| Notifications   | Slack (Block Kit), PagerDuty   |
| Data validation | Pydantic v2                    |
| Logging         | structlog (JSON)               |
| Config          | YAML + pydantic-settings       |
| Packaging       | pyproject.toml / setuptools    |
| Containers      | Docker + Docker Compose        |
