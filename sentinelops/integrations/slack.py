from __future__ import annotations

import structlog
from slack_sdk.web.async_client import AsyncWebClient

from sentinelops.models import Incident, Severity

logger = structlog.get_logger(__name__)


class SlackNotifier:
    """Sends rich Block Kit incident notifications to Slack."""

    def __init__(self, bot_token: str, channel_id: str) -> None:
        self._client = AsyncWebClient(token=bot_token)
        self._channel = channel_id

    async def notify(self, incident: Incident) -> None:
        blocks = self._build_blocks(incident)
        text = f"[{incident.severity.value}] {incident.title}"

        try:
            await self._client.chat_postMessage(
                channel=self._channel,
                text=text,
                blocks=blocks,
            )
            logger.info("slack.notification.sent", incident_id=incident.id)
        except Exception:
            logger.exception("slack.notification.failed", incident_id=incident.id)

    def _build_blocks(self, incident: Incident) -> list[dict]:
        severity_emoji = {
            Severity.P1: ":red_circle:",
            Severity.P2: ":large_orange_circle:",
            Severity.P3: ":large_yellow_circle:",
            Severity.P4: ":white_circle:",
        }

        emoji = severity_emoji.get(incident.severity, ":grey_question:")
        services = ", ".join({a.service for a in incident.anomalies})

        blocks: list[dict] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {incident.severity.value} Incident: {incident.title}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident.id}`"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{incident.severity.value}"},
                    {"type": "mrkdwn", "text": f"*Services:*\n{services}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Detected at:*\n{incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    },
                ],
            },
            {"type": "divider"},
        ]

        # Anomaly details
        for anomaly in incident.anomalies[:5]:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{anomaly.service}* — `{anomaly.metric.value}`\n"
                            f"Current: `{anomaly.current_value:.1f}` | "
                            f"Baseline: `{anomaly.baseline_mean:.1f}` | "
                            f"Z-score: `{anomaly.z_score:.1f}`"
                        ),
                    },
                }
            )

        # AI analysis
        if incident.analysis:
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*AI Analysis* (confidence: {incident.analysis.confidence})\n"
                            f">{incident.analysis.root_cause}"
                        ),
                    },
                },
            ])
            if incident.analysis.remediation_steps:
                steps = "\n".join(
                    f"{i+1}. {step}" for i, step in enumerate(incident.analysis.remediation_steps)
                )
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Suggested Remediation:*\n{steps}"},
                    }
                )

        # Matched runbooks
        if incident.matched_runbooks:
            titles = "\n".join(f"- {rb.title}" for rb in incident.matched_runbooks[:3])
            blocks.extend([
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Related Runbooks:*\n{titles}"},
                },
            ])

        return blocks
