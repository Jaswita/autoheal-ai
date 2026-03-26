"""
AutoHeal AI – Main FastAPI Application
Enhanced for scenario testing, debugging, and UI clarity
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
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
monitor_agent = MonitorAgent()
decision_agent = DecisionAgent()
execution_agent = ExecutionAgent()
verification_agent = VerificationAgent()
audit_agent = AuditAgent()

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def run_pipeline(log: dict) -> dict:
    run_id = str(uuid.uuid4())

    logger.info(f"[RUN START] {run_id}")
    logger.info(f"[INPUT LOG] {log}")

    # Monitor
    monitor_result = monitor_agent.analyze(log)
    logger.info(f"[MONITOR] {monitor_result}")

    # Decision
    decision = decision_agent.decide(monitor_result)
    logger.info(f"[DECISION] {decision}")

    # Execution
    execution = execution_agent.execute(decision)
    logger.info(f"[EXECUTION] {execution}")

    # Verification
    verification = verification_agent.verify(log, decision, execution)
    logger.info(f"[VERIFICATION] {verification}")

    # Audit
    audit_entry = audit_agent.record(
        log, monitor_result, decision, execution, verification, run_id=run_id
    )
    logger.info(f"[AUDIT] Recorded")

    return {
        "run_id": run_id,
        "log": log,
        "monitor": monitor_result,
        "decision": decision,
        "execution": execution,
        "verification": verification,
        "audit_entry": audit_entry,

        # NEW: agent status for UI/debugging
        "agent_status": {
            "monitor": "completed",
            "decision": "completed",
            "execution": "completed",
            "verification": "completed",
            "audit": "completed"
        }
    }

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/run")
def run_system(
    scenario: Optional[str] = Query(
        None,
        description="Scenario: 'high_cpu' | 'service_down' | 'high_memory' | 'healthy' | 'unknown'",
    ),
    service: Optional[str] = Query(None),
):
    """
    Run pipeline with controlled scenarios.
    """

    # Force anomaly except healthy
    force = scenario not in (None, "healthy")

    log = generate_log(
        force_anomaly=force,
        service=service,
        scenario=scenario if scenario != "unknown" else None
    )

    # Inject unknown error manually (AI test)
    if scenario == "unknown":
        log["status"] = "error"
        log["error"] = "unexpected kernel panic in module xyz"

    return run_pipeline(log)


@app.post("/run/custom")
def run_custom(log: dict):
    return run_pipeline(log)


@app.get("/run/batch")
def run_batch(count: int = Query(5, ge=1, le=20)):
    results = []
    for _ in range(count):
        log = generate_log(force_anomaly=True)
        results.append(run_pipeline(log))
    return {"count": count, "results": results}


@app.get("/run/file")
def run_from_file():
    try:
        logs = load_logs_from_file()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="logs.json not found")

    results = [run_pipeline(log) for log in logs]
    return {"count": len(results), "results": results}


@app.get("/audit")
def get_audit(limit: int = Query(50, ge=1, le=200)):
    return {"trail": audit_agent.get_trail(limit), "total": len(audit_agent.trail)}


@app.delete("/audit")
def clear_audit():
    audit_agent.clear()
    return {"message": "Audit trail cleared."}


@app.get("/health")
def health():
    return {"status": "ok"}