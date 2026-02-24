from __future__ import annotations

import json

import anthropic
import structlog

from sentinelops.config import AppConfig
from sentinelops.models import Anomaly, AnalysisResult, CorrelatedEvent, Runbook

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """\
You are an expert SRE incident analyst. You will be given:
1. Detected anomalies (service, metric, z-score, severity)
2. Correlated events across services from the same time window
3. Matching historical runbooks (if any)

Your job:
- Identify the most likely root cause
- Assess your confidence (high/medium/low)
- List the affected services
- Provide concrete, prioritized remediation steps
- Write a one-sentence summary suitable for an incident title

Respond ONLY with valid JSON matching this schema:
{
  "root_cause": "string",
  "confidence": "high|medium|low",
  "affected_services": ["string"],
  "remediation_steps": ["string"],
  "summary": "string"
}"""


class IncidentAnalyzer:
    """Uses Claude to analyze anomalies and generate remediation suggestions."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._client = anthropic.AsyncAnthropic(api_key=config.settings.anthropic_api_key)

    async def analyze(
        self,
        anomalies: list[Anomaly],
        correlated_events: list[CorrelatedEvent],
        runbooks: list[Runbook],
    ) -> AnalysisResult | None:
        if not anomalies:
            return None

        user_message = self._build_context(anomalies, correlated_events, runbooks)

        logger.info("analyzer.request", anomalies=len(anomalies), events=len(correlated_events))

        try:
            response = await self._client.messages.create(
                model=self.config.analyzer_model,
                max_tokens=self.config.analyzer_max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text
            # Strip markdown code fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]  # remove opening ```json
                text = text.rsplit("```", 1)[0]  # remove closing ```
                text = text.strip()
            data = json.loads(text)

            result = AnalysisResult(
                root_cause=data["root_cause"],
                confidence=data["confidence"],
                remediation_steps=data["remediation_steps"],
                affected_services=data["affected_services"],
                summary=data["summary"],
            )
            logger.info("analyzer.complete", confidence=result.confidence)
            return result

        except (json.JSONDecodeError, KeyError, IndexError):
            logger.exception("analyzer.parse_error")
            return None
        except anthropic.APIError:
            logger.exception("analyzer.api_error")
            return None

    def _build_context(
        self,
        anomalies: list[Anomaly],
        correlated_events: list[CorrelatedEvent],
        runbooks: list[Runbook],
    ) -> str:
        sections: list[str] = []

        # Anomalies
        sections.append("## Detected Anomalies")
        for a in anomalies:
            sections.append(
                f"- Service: {a.service} | Metric: {a.metric.value} | "
                f"Value: {a.current_value:.1f} | Baseline: {a.baseline_mean:.1f} +/- {a.baseline_stddev:.1f} | "
                f"Z-score: {a.z_score:.1f} | Severity: {a.severity.value}"
            )

        # Correlated events
        if correlated_events:
            sections.append("\n## Correlated Events Across Services")
            for e in correlated_events[:20]:
                trace = f" [trace: {e.trace_id}]" if e.trace_id else ""
                sections.append(
                    f"- [{e.timestamp.isoformat()}] {e.service} ({e.level}): {e.message}{trace}"
                )

        # Runbooks
        if runbooks:
            sections.append("\n## Similar Past Incidents (Runbooks)")
            for rb in runbooks:
                sections.append(f"### {rb.title}")
                if rb.root_cause:
                    sections.append(f"Root cause: {rb.root_cause}")
                if rb.resolution_steps:
                    for i, step in enumerate(rb.resolution_steps, 1):
                        sections.append(f"  {i}. {step}")

        return "\n".join(sections)
