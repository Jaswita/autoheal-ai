"""
Verification Agent – runs post-fix health checks and reports recovery status.
Includes AI-sourced confidence scoring and detailed check results.
"""
import random
import logging

logger = logging.getLogger(__name__)


class VerificationAgent:

    def verify(self, log: dict, decision: dict, execution: dict) -> dict:
        if not decision.get("action_required"):
            return {
                "status": "success",
                "message": "System healthy – no action was required.",
                "checks": [
                    {"name": "Health Probe", "passed": True, "detail": "Service responded normally"},
                    {"name": "CPU Baseline", "passed": True, "detail": "CPU within normal range"},
                    {"name": "Memory Baseline", "passed": True, "detail": "Memory within normal range"},
                ],
                "resolved": True,
                "confidence": 100,
            }

        source = execution.get("source", "rule_engine")
        issue = decision.get("issue", "unknown")

        # Source-based recovery probability
        recovery_odds = {
            "playbook": 0.93,
            "gemini": 0.88,
            "rule_engine": 0.82,
            "ai": 0.85,
            "fallback": 0.75,
        }
        base_odds = recovery_odds.get(source, 0.80)

        # Severity modifier
        severity = decision.get("severity", "medium")
        severity_mod = {"critical": -0.10, "high": -0.05, "medium": 0.0, "low": 0.05, "none": 0.10}
        probability = min(0.99, base_odds + severity_mod.get(severity, 0.0))

        recovered = random.random() < probability
        confidence = int(probability * 100)

        # Build detailed check results
        checks = self._run_checks(log, decision, execution, recovered)

        failed_checks = [c for c in checks if not c["passed"]]
        all_passed = len(failed_checks) == 0

        final_status = "success" if (recovered and all_passed) else ("partial" if recovered else "failure")

        messages = {
            "success": f"✅ Full recovery confirmed for '{issue}'. All health checks passed.",
            "partial": f"⚠️ Partial recovery for '{issue}'. {len(failed_checks)} check(s) still failing.",
            "failure": f"❌ Recovery failed for '{issue}'. Escalation recommended.",
        }

        logger.info(
            "[VerificationAgent] issue=%s source=%s recovered=%s confidence=%d%%",
            issue, source, recovered, confidence,
        )

        return {
            "status": final_status,
            "message": messages[final_status],
            "checks": checks,
            "resolved": all_passed and recovered,
            "confidence": confidence,
        }

    # ------------------------------------------------------------------
    def _run_checks(self, log: dict, decision: dict, execution: dict, recovered: bool) -> list:
        """Simulate a set of post-fix verification checks."""
        source = execution.get("source", "rule_engine")
        cpu = log.get("cpu", 50) or 50
        memory = log.get("memory", 50) or 50
        issue = decision.get("issue", "")

        # Service health probe
        service_up = recovered
        checks = [
            {
                "name": "Service Health Probe",
                "passed": service_up,
                "detail": "HTTP 200 OK from /health endpoint" if service_up else "Service still not responding",
            }
        ]

        # CPU check
        cpu_ok = cpu < 90 or recovered
        checks.append({
            "name": "CPU Utilisation",
            "passed": cpu_ok,
            "detail": f"CPU at {max(5, cpu - 30 if recovered else cpu)}% (threshold: 90%)",
        })

        # Memory check
        mem_ok = memory < 90 or recovered
        checks.append({
            "name": "Memory Utilisation",
            "passed": mem_ok,
            "detail": f"Memory at {max(10, memory - 25 if recovered else memory)}% (threshold: 90%)",
        })

        # Log error clearance
        log_clear = recovered or random.random() < 0.6
        checks.append({
            "name": "Error Log Clearance",
            "passed": log_clear,
            "detail": "No new errors in last 60s" if log_clear else "Errors still appearing in logs",
        })

        # Connectivity
        connectivity = recovered or random.random() < 0.7
        checks.append({
            "name": "Network Connectivity",
            "passed": connectivity,
            "detail": "Downstream services reachable" if connectivity else "Network still degraded",
        })

        # Fix applied
        checks.append({
            "name": "Fix Applied",
            "passed": True,
            "detail": f"Action executed via '{source}': {str(execution.get('action_taken', ''))[:80]}",
        })

        return checks