"""
Execution Agent – applies fixes for known issues or uses AI fallback.
"""
import logging
from utils.ai_helper import call_ai

logger = logging.getLogger(__name__)

PLAYBOOK = {
    "nginx_down": "systemctl restart nginx",
    "database_down": "systemctl restart postgresql",
    "redis_down": "systemctl restart redis",
    "worker_down": "systemctl restart worker",
    "auth-service_down": "systemctl restart auth-service",
    "message-queue_down": "systemctl restart rabbitmq-server",

    "nginx_high_cpu": "kill $(pgrep -f nginx)",
    "worker_high_cpu": "kill $(pgrep -f worker)",

    "database_high_memory": "free memory and restart db",
    "redis_high_memory": "redis-cli FLUSHDB",
}


class ExecutionAgent:
    def execute(self, decision: dict) -> dict:
        if not decision.get("action_required"):
            return {
                "action_taken": "no_action",
                "source": "playbook",
                "fix_detail": "System healthy",
                "simulated": True,
                "success": True,
            }

        issue = decision.get("issue")

        # ------------------------------
        # 1. Playbook
        # ------------------------------
        if issue in PLAYBOOK:
            logger.info(f"[Execution] Playbook fix for {issue}")
            return {
                "action_taken": PLAYBOOK[issue],
                "source": "playbook",
                "fix_detail": "Rule-based fix applied",
                "simulated": True,
                "success": True,
            }

        # ------------------------------
        # 2. AI fallback (SIMULATED)
        # ------------------------------
        details = decision.get("details", {})

        context = {
            "service": details.get("service") or issue.split("_")[0],
            "error": details.get("error"),
            "cpu": details.get("cpu"),
            "memory": details.get("memory"),
        }

        logger.info(f"[Execution] AI simulated fix for {issue}")

        ai = call_ai(context)

        return {
            "action_taken": ai.get("fix"),
            "source": "ai",
            "fix_detail": ai.get("explanation"),
            "simulated": True,
            "success": True,
        }