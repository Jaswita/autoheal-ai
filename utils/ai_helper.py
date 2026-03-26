"""
AI Helper – Simulated AI response generator (no external API).
"""

def call_ai(context: dict) -> dict:
    service = context.get("service", "service")
    error = str(context.get("error", "")).lower()
    cpu = context.get("cpu", 0)
    memory = context.get("memory", 0)

    # ------------------------------------------------------------------
    # Simulated intelligent reasoning
    # ------------------------------------------------------------------

    if "kernel" in error:
        fix = f"Restart {service} service and inspect kernel logs for root cause."
        explanation = "Kernel-level failure detected. Restart and deep log inspection required."

    elif "timeout" in error:
        fix = f"Restart {service} and increase timeout configuration."
        explanation = "Timeout indicates latency or service overload."

    elif cpu and cpu > 90:
        fix = f"Throttle CPU usage or restart {service}."
        explanation = "High CPU usage detected. Resource contention likely."

    elif memory and memory > 90:
        fix = f"Free memory and restart {service}."
        explanation = "Memory exhaustion detected."

    else:
        fix = f"Restart {service} service and monitor logs."
        explanation = "Unknown anomaly detected. Basic recovery applied."

    return {
        "fix": f"AI Suggestion: {fix}",
        "explanation": explanation,
        "source": "ai"   # IMPORTANT: so UI counts AI fixes
    }