from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    elasticsearch_url: str = "https://localhost:9200"
    elasticsearch_api_key: str = ""

    anthropic_api_key: str = ""

    slack_bot_token: str = ""
    slack_channel_id: str = ""

    pagerduty_api_key: str = ""
    pagerduty_service_id: str = ""

    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


class AppConfig:
    """Full application config: YAML file values + environment secrets."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                self._data: dict[str, Any] = yaml.safe_load(f) or {}
        else:
            self._data = {}

        self.settings = Settings()

    # --- Polling ---
    @property
    def poll_interval(self) -> int:
        return self._data.get("polling", {}).get("interval_seconds", 30)

    @property
    def lookback_minutes(self) -> int:
        return self._data.get("polling", {}).get("lookback_minutes", 5)

    # --- Detection ---
    @property
    def thresholds(self) -> dict[str, float]:
        defaults = {"p1": 5.0, "p2": 3.5, "p3": 2.5, "p4": 2.0}
        return self._data.get("detection", {}).get("thresholds", defaults)

    @property
    def baseline_window_minutes(self) -> int:
        return self._data.get("detection", {}).get("baseline_window_minutes", 60)

    @property
    def min_data_points(self) -> int:
        return self._data.get("detection", {}).get("min_data_points", 10)

    # --- Correlation ---
    @property
    def correlation_window_minutes(self) -> int:
        return self._data.get("correlation", {}).get("window_minutes", 10)

    @property
    def max_correlated_events(self) -> int:
        return self._data.get("correlation", {}).get("max_events", 50)

    # --- Incidents ---
    @property
    def dedup_cooldown_minutes(self) -> int:
        return self._data.get("incidents", {}).get("dedup_cooldown_minutes", 30)

    @property
    def pagerduty_severities(self) -> list[str]:
        return self._data.get("incidents", {}).get("pagerduty_severities", ["P1", "P2"])

    # --- Elasticsearch indices ---
    @property
    def log_index(self) -> str:
        return self._data.get("elasticsearch", {}).get("log_index", "app-logs-*")

    @property
    def metrics_index(self) -> str:
        return self._data.get("elasticsearch", {}).get("metrics_index", "app-metrics-*")

    @property
    def runbook_index(self) -> str:
        return self._data.get("elasticsearch", {}).get("runbook_index", "incident-runbooks")

    # --- Analyzer ---
    @property
    def analyzer_model(self) -> str:
        return self._data.get("analyzer", {}).get("model", "claude-sonnet-4-6")

    @property
    def analyzer_max_tokens(self) -> int:
        return self._data.get("analyzer", {}).get("max_tokens", 1024)
