"""
Verification Agent – confirms whether the issue has been resolved.

In a real system this would re-poll the service endpoint / metrics.
Here we simulate verification using the same thresholds as the Monitor Agent
and a probabilistic model that matches the fix confidence.
"""
import logging
import random

logger = logging.getLogger(__name__)

CPU_OK_THRESHOLD = 80
MEMORY_OK_THRESHOLD = 80


class VerificationAgent:
    """Checks whether the executed fix resolved the anomaly."""

    def verify(self, log: dict, decision: dict, execution: dict) -> dict:
        """
        Args:
            log:       original log entry
            decision:  output from DecisionAgent
            execution: output from ExecutionAgent

        Returns:
            {
                "status": "success" | "failure" | "partial",
                "message": str,
                "checks": list[dict],
                "resolved": bool
            }
        """
        if not decision.get("action_required"):
            return {
                "status": "success",
                "message": "No anomaly detected – system was already healthy.",
                "checks": [],
                "resolved": True,
            }

        issue = decision.get("issue", "unknown")
        source = execution.get("source", "unknown")
        checks = []

        # Simulate post-fix metrics (realistic improvement after fix)
        original_cpu = int(log.get("cpu") or 0)
        original_memory = int(log.get("memory") or 0)
        original_status = str(log.get("status", "running")).lower()

        # After a playbook fix, there's a 92 % chance of recovery
        # After an AI fix, there's a 78 % chance
        # After a fallback, there's a 65 % chance
        recovery_odds = {"playbook": 0.92, "gemini": 0.78, "fallback": 0.65}
        recovered = random.random() < recovery_odds.get(source, 0.75)

        # Simulate new post-fix metrics
        new_cpu = max(original_cpu - random.randint(40, 70), random.randint(5, 30)) if recovered else original_cpu
        new_memory = max(original_memory - random.randint(30, 60), random.randint(10, 40)) if recovered else original_memory
        new_status = "running" if recovered else original_status

        # CPU check
        cpu_ok = new_cpu < CPU_OK_THRESHOLD
        checks.append({
            "check": "cpu_usage",
            "before": f"{original_cpu}%",
            "after": f"{new_cpu}%",
            "passed": cpu_ok,
        })

        # Memory check
        mem_ok = new_memory < MEMORY_OK_THRESHOLD
        checks.append({
            "check": "memory_usage",
            "before": f"{original_memory}%",
            "after": f"{new_memory}%",
            "passed": mem_ok,
        })

        # Service status check
        status_ok = new_status == "running"
        checks.append({
            "check": "service_status",
            "before": original_status,
            "after": new_status,
            "passed": status_ok,
        })

        all_ok = all(c["passed"] for c in checks)
        some_ok = any(c["passed"] for c in checks)
        overall = "success" if all_ok else ("partial" if some_ok else "failure")

        logger.info("[VerificationAgent] Issue '%s' verification result: %s", issue, overall)

        return {
            "status": overall,
            "message": (
                f"Issue '{issue}' successfully resolved." if all_ok
                else f"Partial recovery for '{issue}' – some checks failed."
                if some_ok
                else f"Fix for '{issue}' did not resolve the issue. Manual intervention may be required."
            ),
            "checks": checks,
            "resolved": all_ok,
        }
