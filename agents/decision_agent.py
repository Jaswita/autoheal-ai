"""
Decision Agent – classifies issues and decides actions.
"""
import logging

logger = logging.getLogger(__name__)

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


class DecisionAgent:

    def decide(self, monitor_result: dict) -> dict:

        if not monitor_result.get("anomaly_detected"):
            return {
                "issue": "none",
                "severity": "none",
                "action_required": False,
                "recommended_action": "no_action",
                "details": {},
            }

        log = monitor_result.get("log", {})
        anomalies = monitor_result.get("anomalies", [])

        issue, severity, action = self._classify(log, anomalies)

        logger.info(f"[Decision] {issue} | {severity}")

        return {
            "issue": issue,
            "severity": severity,
            "action_required": True,
            "recommended_action": action,
            "details": log,
        }

    def _classify(self, log, anomalies):
        service = log.get("service", "unknown")
        cpu = int(log.get("cpu") or 0)
        memory = int(log.get("memory") or 0)
        status = str(log.get("status", "")).lower()
        error = (log.get("error") or "").lower()

        # Unknown (AI case)
        if status == "error" and error:
            return f"{service}_unknown_issue", SEVERITY_HIGH, f"investigate_{service}_with_ai"

        # Service down
        if status == "down":
            return f"{service}_down", SEVERITY_HIGH, f"restart_{service}"

        # High memory
        if memory > 90:
            return f"{service}_high_memory", SEVERITY_HIGH, f"reduce_memory_{service}"

        # High CPU
        if cpu > 90:
            return f"{service}_high_cpu", SEVERITY_HIGH, f"throttle_cpu_{service}"

        return f"{service}_error", SEVERITY_LOW, f"investigate_{service}"