from __future__ import annotations

import asyncio
import signal
import sys

import structlog
import uvicorn
from dotenv import load_dotenv

from sentinelops.analyzer import IncidentAnalyzer
from sentinelops.config import AppConfig
from sentinelops.correlator import EventCorrelator
from sentinelops.detector import AnomalyDetector
from sentinelops.incidents import IncidentManager
from sentinelops.models import Incident
from sentinelops.integrations.elasticsearch import ElasticsearchClient
from sentinelops.integrations.pagerduty import PagerDutyNotifier
from sentinelops.integrations.slack import SlackNotifier
from sentinelops.runbooks import RunbookSearch
from sentinelops.store import incident_store
from sentinelops.utils.logging import setup_logging

logger = structlog.get_logger(__name__)


class SentinelOps:
    """Main application: wires all components and runs the polling loop."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._running = False

        # Core components
        self.es = ElasticsearchClient(
            url=config.settings.elasticsearch_url,
            api_key=config.settings.elasticsearch_api_key,
        )
        self.detector = AnomalyDetector(config, self.es)
        self.correlator = EventCorrelator(config, self.es)
        self.runbook_search = RunbookSearch(config, self.es)
        self.analyzer = IncidentAnalyzer(config)
        self.incident_manager = IncidentManager(config)

        # Notification channels
        self.slack: SlackNotifier | None = None
        if config.settings.slack_bot_token:
            self.slack = SlackNotifier(
                bot_token=config.settings.slack_bot_token,
                channel_id=config.settings.slack_channel_id,
            )

        self.pagerduty: PagerDutyNotifier | None = None
        if config.settings.pagerduty_api_key:
            self.pagerduty = PagerDutyNotifier(
                api_key=config.settings.pagerduty_api_key,
                service_id=config.settings.pagerduty_service_id,
            )

    async def start(self) -> None:
        """Start the polling loop."""
        self._running = True
        logger.info(
            "sentinelops.starting",
            poll_interval=self.config.poll_interval,
            slack_enabled=self.slack is not None,
            pagerduty_enabled=self.pagerduty is not None,
        )

        try:
            while self._running:
                await self._tick()
                self.incident_manager.cleanup_stale_entries()
                await asyncio.sleep(self.config.poll_interval)
        finally:
            await self.es.close()
            logger.info("sentinelops.stopped")

    def stop(self) -> None:
        self._running = False

    async def _tick(self) -> None:
        """Single detection -> correlation -> analysis -> incident -> notify cycle."""
        try:
            # 1. Detect anomalies
            anomalies = await self.detector.detect()
            if not anomalies:
                return

            # 2. Correlate related events
            correlated_events = await self.correlator.correlate(anomalies)

            # 3. Search runbooks
            runbooks = await self.runbook_search.find_matching(anomalies)

            # 4. AI analysis
            analysis = await self.analyzer.analyze(anomalies, correlated_events, runbooks)

            # 5. Create incident (with dedup)
            incident = self.incident_manager.create_incident(
                anomalies=anomalies,
                correlated_events=correlated_events,
                runbooks=runbooks,
                analysis=analysis,
            )

            if incident is None:
                return

            # 6. Store for dashboard
            incident_store.add(incident)

            # 7. Dispatch notifications
            await self._notify(incident)

        except Exception:
            logger.exception("sentinelops.tick.error")

    async def _notify(self, incident: Incident) -> None:
        tasks: list[asyncio.Task] = []

        if self.slack:
            tasks.append(asyncio.create_task(self.slack.notify(incident)))

        if self.pagerduty and incident.severity.value in self.config.pagerduty_severities:
            tasks.append(asyncio.create_task(self.pagerduty.notify(incident)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


async def run(config_path: str = "config.yaml") -> None:
    load_dotenv()
    config = AppConfig(config_path)
    setup_logging(debug=config.settings.debug)

    app = SentinelOps(config)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, app.stop)

    # Start API server and polling loop concurrently
    from sentinelops.api import app as api_app

    api_config = uvicorn.Config(api_app, host="0.0.0.0", port=8000, log_level="warning")
    api_server = uvicorn.Server(api_config)

    logger.info("sentinelops.dashboard", url="http://localhost:8000")

    await asyncio.gather(
        app.start(),
        api_server.serve(),
    )


def cli_entry() -> None:
    """CLI entrypoint for `sentinelops` command."""
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    asyncio.run(run(config_path))


if __name__ == "__main__":
    cli_entry()
