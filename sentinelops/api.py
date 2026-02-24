from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sentinelops.store import incident_store

app = FastAPI(title="SentinelOps", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent.parent / "web" / "dist"


# ── API Routes ─────────────────────────────────────────────────

@app.get("/api/incidents")
def list_incidents(limit: int = 50, offset: int = 0):
    incidents = incident_store.list_all(limit=limit, offset=offset)
    return {
        "total": incident_store.count(),
        "incidents": [_serialize_incident(inc) for inc in incidents],
    }


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    inc = incident_store.get(incident_id)
    if inc is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _serialize_incident(inc, full=True)


@app.get("/api/services")
def list_services():
    return {"services": incident_store.get_service_summary()}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "incidents_tracked": incident_store.count()}


# ── Serialization ──────────────────────────────────────────────

def _serialize_incident(inc, full: bool = False) -> dict:
    data = {
        "id": inc.id,
        "title": inc.title,
        "severity": inc.severity.value,
        "created_at": inc.created_at.isoformat(),
        "dedup_key": inc.dedup_key,
        "services": sorted({a.service for a in inc.anomalies}),
        "anomaly_count": len(inc.anomalies),
        "has_analysis": inc.analysis is not None,
    }

    if inc.analysis:
        data["root_cause"] = inc.analysis.root_cause
        data["confidence"] = inc.analysis.confidence

    if full:
        data["anomalies"] = [
            {
                "service": a.service,
                "metric": a.metric.value,
                "current_value": a.current_value,
                "baseline_mean": a.baseline_mean,
                "baseline_stddev": a.baseline_stddev,
                "z_score": a.z_score,
                "severity": a.severity.value,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in inc.anomalies
        ]
        data["correlated_events"] = [
            {
                "service": e.service,
                "level": e.level,
                "message": e.message,
                "timestamp": e.timestamp.isoformat(),
                "trace_id": e.trace_id,
            }
            for e in inc.correlated_events[:30]
        ]
        data["matched_runbooks"] = [
            {
                "title": rb.title,
                "root_cause": rb.root_cause,
                "resolution_steps": rb.resolution_steps,
                "services_affected": rb.services_affected,
                "score": rb.score,
            }
            for rb in inc.matched_runbooks
        ]
        if inc.analysis:
            data["analysis"] = {
                "root_cause": inc.analysis.root_cause,
                "confidence": inc.analysis.confidence,
                "remediation_steps": inc.analysis.remediation_steps,
                "affected_services": inc.analysis.affected_services,
                "summary": inc.analysis.summary,
            }

    return data


# ── Static file serving (React SPA) ───────────────────────────

def mount_static():
    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{path:path}")
        def serve_spa(path: str):
            file_path = STATIC_DIR / path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(STATIC_DIR / "index.html")


mount_static()
