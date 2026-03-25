"""
Execution Agent – applies fixes for known issues (rule-based) or delegates
unknown issues to the AI Helper (Gemini).
"""
import logging
from utils.ai_helper import call_ai

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rule-based playbook  (issue_key → command / action string)
# ---------------------------------------------------------------------------
PLAYBOOK: dict[str, str] = {
    # nginx
    "nginx_down":                       "systemctl restart nginx",
    "nginx_timeout":                    "systemctl reload nginx && systemctl restart nginx",
    "nginx_ssl_error":                  "certbot renew && systemctl reload nginx",
    # database
    "database_down":                    "systemctl restart postgresql",
    "database_oom":                     "sysctl -w vm.drop_caches=3 && systemctl restart postgresql",
    "database_disk_full":               "find /var/log -name '*.log' -mtime +7 -delete && systemctl restart postgresql",
    "database_high_memory":             "psql -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle';\" && systemctl reload postgresql",
    # api-gateway
    "api-gateway_down":                 "systemctl restart api-gateway",
    "api-gateway_high_cpu":             "systemctl restart api-gateway && echo 'scale_out=true' >> /etc/api-gateway/config",
    "api-gateway_ssl_error":            "certbot renew && systemctl reload api-gateway",
    # redis
    "redis_down":                       "systemctl restart redis",
    "redis_high_memory":                "redis-cli FLUSHDB && systemctl restart redis",
    # worker
    "worker_down":                      "systemctl restart worker",
    "worker_timeout":                   "systemctl stop worker && sleep 2 && systemctl start worker",
    "worker_high_cpu":                  "kill $(pgrep -f worker) && systemctl start worker",
    # auth-service
    "auth-service_down":                "systemctl restart auth-service",
    "auth-service_ssl_error":           "certbot renew --cert-name auth-service && systemctl reload auth-service",
    # message-queue
    "message-queue_down":               "systemctl restart rabbitmq-server",
    # generic high resource
    "high_cpu":                         "top -bn1 | grep 'Cpu' && kill $(ps aux --sort=-%cpu | awk 'NR==2{print $2}')",
    "high_memory":                      "sync; echo 3 > /proc/sys/vm/drop_caches",
}


class ExecutionAgent:
    """Executes a fix – either from the playbook or from the AI helper."""

    def execute(self, decision: dict) -> dict:
        """
        Args:
            decision: output from DecisionAgent.decide()

        Returns:
            {
                "action_taken": str,
                "source": "playbook" | "ai" | "fallback",
                "fix_detail": str,
                "simulated": bool,
                "success": bool
            }
        """
        if not decision.get("action_required"):
            return {
                "action_taken": "no_action",
                "source": "playbook",
                "fix_detail": "System healthy – no action required.",
                "simulated": True,
                "success": True,
            }

        issue = decision.get("issue", "unknown")
        details = decision.get("details", {})

        # --- Try the static playbook first ---
        command = PLAYBOOK.get(issue)
        if command:
            logger.info("[ExecutionAgent] Playbook hit for issue '%s': %s", issue, command)
            return {
                "action_taken": command,
                "source": "playbook",
                "fix_detail": f"Playbook fix applied for '{issue}'.",
                "simulated": True,   # In a real deployment, os.system(command) would run here
                "success": True,
            }

        # --- Fall through to recommended_action key ---
        recommended = decision.get("recommended_action", "")
        command = PLAYBOOK.get(recommended)
        if command:
            logger.info("[ExecutionAgent] Playbook hit for recommended_action '%s'", recommended)
            return {
                "action_taken": command,
                "source": "playbook",
                "fix_detail": f"Playbook fix applied via recommended_action '{recommended}'.",
                "simulated": True,
                "success": True,
            }

        # --- AI-generated fix for unknown issues ---
        logger.info("[ExecutionAgent] No playbook entry for '%s' – calling AI helper.", issue)
        ai_result = call_ai({
            "issue": issue,
            "recommended_action": recommended,
            **details,
        })

        return {
            "action_taken": ai_result.get("fix", "manual_intervention_required"),
            "source": ai_result.get("source", "fallback"),
            "fix_detail": ai_result.get("explanation", ""),
            "simulated": True,
            "success": True,
        }
