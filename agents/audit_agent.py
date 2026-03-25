"""
Audit Agent – records every step of the pipeline and maintains an in-memory
audit trail that is also persisted to a JSON file on disk.
"""
import json
import logging
import os
import datetime
from typing import Optional

logger = logging.getLogger(__name__)

AUDIT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "audit_trail.json")


class AuditAgent:
    """Stores and retrieves audit records for every pipeline run."""

    def __init__(self, persist: bool = True):
        self.trail: list[dict] = []
        self.persist = persist
        self._load_existing()

    # ------------------------------------------------------------------
    def record(
        self,
        log: dict,
        monitor_result: dict,
        decision: dict,
        execution: dict,
        verification: dict,
        run_id: Optional[str] = None,
    ) -> dict:
        """
        Build a full audit record and append it to the trail.

        Returns the created audit entry.
        """
        entry = {
            "run_id": run_id or self._generate_run_id(),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "input_log": log,
            "monitor": {
                "anomaly_detected": monitor_result.get("anomaly_detected"),
                "anomalies": monitor_result.get("anomalies", []),
            },
            "decision": {
                "issue": decision.get("issue"),
                "severity": decision.get("severity"),
                "action_required": decision.get("action_required"),
                "recommended_action": decision.get("recommended_action"),
            },
            "execution": {
                "action_taken": execution.get("action_taken"),
                "source": execution.get("source"),
                "fix_detail": execution.get("fix_detail"),
                "simulated": execution.get("simulated", True),
            },
            "verification": {
                "status": verification.get("status"),
                "resolved": verification.get("resolved"),
                "message": verification.get("message"),
                "checks": verification.get("checks", []),
            },
        }

        self.trail.append(entry)
        logger.info("[AuditAgent] Recorded run_id=%s status=%s", entry["run_id"], verification.get("status"))

        if self.persist:
            self._save()

        return entry

    def get_trail(self, limit: int = 50) -> list:
        """Return the most recent `limit` audit entries (newest first)."""
        return list(reversed(self.trail[-limit:]))

    def clear(self):
        """Clear the in-memory trail and the persisted file."""
        self.trail = []
        if self.persist and os.path.exists(AUDIT_FILE):
            os.remove(AUDIT_FILE)

    # ------------------------------------------------------------------
    def _generate_run_id(self) -> str:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"run_{ts}"

    def _save(self):
        try:
            os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
            with open(AUDIT_FILE, "w") as f:
                json.dump(self.trail, f, indent=2)
        except Exception as exc:
            logger.warning("[AuditAgent] Failed to persist audit trail: %s", exc)

    def _load_existing(self):
        if self.persist and os.path.exists(AUDIT_FILE):
            try:
                with open(AUDIT_FILE, "r") as f:
                    self.trail = json.load(f)
                logger.info("[AuditAgent] Loaded %d existing audit records.", len(self.trail))
            except Exception:
                self.trail = []
