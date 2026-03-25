"""
Decision Agent – classifies the type of issue and decides the required action.
"""
import logging

logger = logging.getLogger(__name__)

# Severity levels
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"


class DecisionAgent:
    """Analyses anomalies detected by the Monitor Agent and produces a decision."""

    def decide(self, monitor_result: dict) -> dict:
        """
        Args:
            monitor_result: output from MonitorAgent.analyze()

        Returns:
            {
                "issue": str,
                "severity": str,
                "action_required": bool,
                "recommended_action": str,
                "details": dict
            }
        """
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

        issue, severity, recommended_action = self._classify(log, anomalies)

        logger.info(
            "[DecisionAgent] Issue=%s | Severity=%s | Action=%s",
            issue, severity, recommended_action,
        )

        return {
            "issue": issue,
            "severity": severity,
            "action_required": True,
            "recommended_action": recommended_action,
            "details": {
                "service": log.get("service"),
                "host": log.get("host"),
                "cpu": log.get("cpu"),
                "memory": log.get("memory"),
                "error": log.get("error"),
                "anomalies": anomalies,
            },
        }

    # ------------------------------------------------------------------
    def _classify(self, log: dict, anomalies: list) -> tuple:
        service = log.get("service", "unknown")
        cpu = int(log.get("cpu") or 0)
        memory = int(log.get("memory") or 0)
        status = str(log.get("status", "")).lower()
        error = (log.get("error") or "").lower()

        # Service down takes highest priority
        if status == "down":
            issue = f"{service}_down"
            severity = SEVERITY_HIGH
            action = f"restart_{service}"
            # Specialise based on error type
            if "memory" in error or "oom" in error:
                issue = f"{service}_oom"
                action = f"free_memory_and_restart_{service}"
                severity = SEVERITY_HIGH
            elif "disk" in error:
                issue = f"{service}_disk_full"
                action = "clear_disk_space"
                severity = SEVERITY_HIGH
            elif "certificate" in error or "ssl" in error:
                issue = f"{service}_ssl_error"
                action = "renew_ssl_certificate"
                severity = SEVERITY_MEDIUM
            elif "timeout" in error:
                issue = f"{service}_timeout"
                action = f"increase_timeout_and_restart_{service}"
                severity = SEVERITY_MEDIUM
            return issue, severity, action

        # High memory (service still running)
        if memory > 90:
            return (
                f"{service}_high_memory",
                SEVERITY_HIGH if memory > 95 else SEVERITY_MEDIUM,
                f"reduce_memory_{service}",
            )

        # High CPU
        if cpu > 90:
            return (
                f"{service}_high_cpu",
                SEVERITY_HIGH if cpu > 95 else SEVERITY_MEDIUM,
                f"throttle_cpu_{service}",
            )

        # Generic anomaly / error logged
        return (
            f"{service}_error",
            SEVERITY_LOW,
            f"investigate_{service}",
        )
