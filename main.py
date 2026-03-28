"""
AutoHeal AI – Main FastAPI Application
Real Gemini API integration + enhanced endpoints
"""
import logging
import os
import uuid
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.monitor_agent import MonitorAgent
from agents.decision_agent import DecisionAgent
from agents.execution_agent import ExecutionAgent
from agents.verification_agent import VerificationAgent
from agents.audit_agent import AuditAgent
from utils.log_simulator import generate_log, load_logs_from_file
from utils.ai_helper import call_ai_freeform, GEMINI_API_KEY, _HTTPX_AVAILABLE

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
    description="Multi-Agent Autonomous Workflow Recovery System with Gemini AI",
    version="2.0.0",
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
monitor_agent    = MonitorAgent()
decision_agent   = DecisionAgent()
execution_agent  = ExecutionAgent()
verification_agent = VerificationAgent()
audit_agent      = AuditAgent()

# ---------------------------------------------------------------------------
# In-memory stats tracker
# ---------------------------------------------------------------------------
_stats = {
    "total_runs": 0,
    "ai_fixes": 0,
    "playbook_fixes": 0,
    "resolved": 0,
    "unresolved": 0,
    "gemini_calls": 0,
    "rule_engine_calls": 0,
}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def run_pipeline(log: dict) -> dict:
    run_id = str(uuid.uuid4())
    logger.info(f"[RUN START] {run_id}")
    logger.info(f"[INPUT LOG] {log}")

    monitor_result  = monitor_agent.analyze(log)
    decision        = decision_agent.decide(monitor_result)
    execution       = execution_agent.execute(decision)
    verification    = verification_agent.verify(log, decision, execution)

    audit_entry = audit_agent.record(
        log, monitor_result, decision, execution, verification, run_id=run_id
    )

    # Update global stats
    _stats["total_runs"] += 1
    src = execution.get("source", "")
    if src in ("gemini",):
        _stats["ai_fixes"] += 1
        _stats["gemini_calls"] += 1
    elif src in ("rule_engine", "fallback", "ai"):
        _stats["ai_fixes"] += 1
        _stats["rule_engine_calls"] += 1
    else:
        _stats["playbook_fixes"] += 1

    if verification.get("resolved"):
        _stats["resolved"] += 1
    else:
        _stats["unresolved"] += 1

    logger.info(f"[RUN COMPLETE] {run_id}")

    return {
        "run_id": run_id,
        "log": log,
        "monitor": monitor_result,
        "decision": decision,
        "execution": execution,
        "verification": verification,
        "audit_entry": audit_entry,
        "agent_status": {
            "monitor":      "completed",
            "decision":     "completed",
            "execution":    "completed",
            "verification": "completed",
            "audit":        "completed",
        },
        "ai_powered": execution.get("source") in ("gemini", "rule_engine", "ai"),
    }


# ---------------------------------------------------------------------------
# Request model for AI chat
# ---------------------------------------------------------------------------
class AIAnalyzeRequest(BaseModel):
    prompt: str


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
    force = scenario not in (None, "healthy")
    log = generate_log(
        force_anomaly=force,
        service=service,
        scenario=scenario if scenario != "unknown" else None,
    )
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
    # Reset stats too
    for k in _stats:
        _stats[k] = 0
    return {"message": "Audit trail and stats cleared."}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_configured": bool(GEMINI_API_KEY),
        "httpx_available": _HTTPX_AVAILABLE,
        "ai_mode": "gemini" if (GEMINI_API_KEY and _HTTPX_AVAILABLE) else "rule_engine",
    }


@app.get("/stats")
def get_stats():
    """Live statistics for the dashboard."""
    total = _stats["total_runs"] or 1  # avoid div/0
    return {
        **_stats,
        "resolution_rate": round(_stats["resolved"] / total * 100, 1),
        "ai_fix_rate": round(_stats["ai_fixes"] / total * 100, 1),
        "gemini_active": bool(GEMINI_API_KEY and _HTTPX_AVAILABLE),
    }


@app.post("/ai/analyze")
def ai_analyze(body: AIAnalyzeRequest):
    """
    Free-form AI chat endpoint.
    Routes directly to Gemini 1.5 Flash (or rule-engine fallback).
    """
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    answer = call_ai_freeform(body.prompt)
    return {
        "prompt": body.prompt,
        "response": answer,
        "model": "gemini-2.5-flash" if (GEMINI_API_KEY and _HTTPX_AVAILABLE) else "rule_engine_fallback",
    }