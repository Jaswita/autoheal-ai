"""
Execution Agent – applies fixes for known issues or uses AI (Gemini/rule-engine) fallback.
"""
import logging
from utils.ai_helper import call_ai

logger = logging.getLogger(__name__)

PLAYBOOK = {
    "nginx_down":              "systemctl restart nginx",
    "database_down":           "systemctl restart postgresql",
    "redis_down":              "systemctl restart redis",
    "worker_down":             "systemctl restart worker",
    "auth-service_down":       "systemctl restart auth-service",
    "message-queue_down":      "systemctl restart rabbitmq-server",
    "api-gateway_down":        "systemctl restart api-gateway",

    "nginx_high_cpu":          "renice -n 15 $(pgrep nginx) && systemctl restart nginx",
    "worker_high_cpu":         "renice -n 15 $(pgrep worker) && systemctl restart worker",
    "api-gateway_high_cpu":    "systemctl restart api-gateway",

    "database_high_memory":    "sync && echo 3 > /proc/sys/vm/drop_caches && systemctl restart postgresql",
    "redis_high_memory":       "redis-cli FLUSHDB && systemctl restart redis",
    "worker_high_memory":      "systemctl restart worker",
}


class ExecutionAgent:
    def execute(self, decision: dict) -> dict:
        if not decision.get("action_required"):
            return {
                "action_taken": "no_action",
                "source": "playbook",
                "fix_detail": "System is healthy — no intervention needed.",
                "preventive_measure": "Continue monitoring at regular intervals.",
                "severity": "none",
                "estimated_recovery_time": "N/A",
                "simulated": True,
                "success": True,
            }

        issue = decision.get("issue", "")

        # ── 1. Rule-based playbook ────────────────────────────────────────
        if issue in PLAYBOOK:
            logger.info(f"[ExecutionAgent] Playbook fix for '{issue}'")
            return {
                "action_taken": PLAYBOOK[issue],
                "source": "playbook",
                "fix_detail": f"Known playbook fix applied for issue: {issue}",
                "preventive_measure": "Review runbook and add health-check alerting for this service.",
                "severity": decision.get("severity", "high"),
                "estimated_recovery_time": "15–30 seconds",
                "simulated": True,
                "success": True,
            }

        # ── 2. AI fallback (Gemini or rule-engine) ────────────────────────
        details = decision.get("details", {})
        context = {
            "service":  details.get("service") or issue.split("_")[0],
            "status":   details.get("status", "error"),
            "error":    details.get("error"),
            "cpu":      details.get("cpu"),
            "memory":   details.get("memory"),
            "host":     details.get("host", "unknown"),
        }

        logger.info(f"[ExecutionAgent] Calling AI for unknown issue '{issue}'")
        ai = call_ai(context)

        return {
            "action_taken":           ai.get("fix"),
            "source":                 ai.get("source", "rule_engine"),
            "fix_detail":             ai.get("explanation"),
            "preventive_measure":     ai.get("preventive_measure", "Monitor and alert proactively."),
            "severity":               ai.get("severity", decision.get("severity", "high")),
            "estimated_recovery_time": ai.get("estimated_recovery_time", "30–90 seconds"),
            "simulated": True,
            "success":   True,
        }