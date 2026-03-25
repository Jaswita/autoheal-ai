"""
AutoHeal AI – Main FastAPI Application
Connects all agents into a full pipeline and exposes REST endpoints.
"""
import logging
import os
import uuid
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from agents.monitor_agent import MonitorAgent
from agents.decision_agent import DecisionAgent
from agents.execution_agent import ExecutionAgent
from agents.verification_agent import VerificationAgent
from agents.audit_agent import AuditAgent
from utils.log_simulator import generate_log, load_logs_from_file

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
)
logger = logging.getLogger("autoheal")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AutoHeal AI",
    description="Multi-Agent Autonomous Workflow Recovery System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount static frontend
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ---------------------------------------------------------------------------
# Agent singletons
# ---------------------------------------------------------------------------
monitor_agent    = MonitorAgent()
decision_agent   = DecisionAgent()
execution_agent  = ExecutionAgent()
verification_agent = VerificationAgent()
audit_agent      = AuditAgent()


# ---------------------------------------------------------------------------
# Helper: run full pipeline on one log entry
# ---------------------------------------------------------------------------
def run_pipeline(log: dict) -> dict:
    run_id = str(uuid.uuid4())

    monitor_result  = monitor_agent.analyze(log)
    decision        = decision_agent.decide(monitor_result)
    execution       = execution_agent.execute(decision)
    verification    = verification_agent.verify(log, decision, execution)
    audit_entry     = audit_agent.record(
        log, monitor_result, decision, execution, verification, run_id=run_id
    )

    return {
        "run_id": run_id,
        "log": log,
        "monitor": monitor_result,
        "decision": decision,
        "execution": execution,
        "verification": verification,
        "audit_entry": audit_entry,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Serve the frontend dashboard."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)


@app.get("/run")
def run_system(
    scenario: Optional[str] = Query(
        None,
        description="Scenario override: 'high_cpu' | 'service_down' | 'high_memory' | 'healthy'",
    ),
    service: Optional[str] = Query(None, description="Pin a specific service name"),
):
    """
    Trigger the full AutoHeal pipeline on a freshly generated log.

    Returns the complete pipeline result including log, decision, action,
    verification, and audit entry.
    """
    log = generate_log(
        force_anomaly=(scenario not in (None, "healthy")),
        service=service,
        scenario=scenario,
    )
    return run_pipeline(log)


@app.post("/run/custom")
def run_custom(log: dict):
    """
    Run the pipeline with a user-supplied log entry (JSON body).
    Useful for testing specific scenarios.
    """
    return run_pipeline(log)


@app.get("/run/batch")
def run_batch(
    count: int = Query(5, ge=1, le=20, description="Number of logs to process (1-20)"),
):
    """Process multiple simulated logs in one request."""
    results = []
    for _ in range(count):
        log = generate_log(force_anomaly=True)
        results.append(run_pipeline(log))
    return {"count": count, "results": results}


@app.get("/run/file")
def run_from_file():
    """Process all log entries from data/logs.json."""
    try:
        logs = load_logs_from_file()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="data/logs.json not found")
    results = [run_pipeline(log) for log in logs]
    return {"count": len(results), "results": results}


@app.get("/audit")
def get_audit(limit: int = Query(50, ge=1, le=200)):
    """Return the most recent audit trail entries."""
    return {"trail": audit_agent.get_trail(limit=limit), "total": len(audit_agent.trail)}


@app.delete("/audit")
def clear_audit():
    """Clear the audit trail (in-memory and persisted file)."""
    audit_agent.clear()
    return {"message": "Audit trail cleared."}


@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "service": "AutoHeal AI"}
