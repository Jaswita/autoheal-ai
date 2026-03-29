"""
AI Helper – Google Gemini 1.5 Flash via direct REST API (httpx).
No SDK dependency; works with any Python version and Pydantic v2.
Falls back to a rich rule-based engine when the API key is absent or call fails.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBpXjIeIEbc9XtjSd7Chh_6UJdJ-tm9cJs")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

# Try to import httpx (bundled with uvicorn[standard])
try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    logger.warning("[AI] httpx not installed - using rule-based fallback only.")

_SDK_AVAILABLE = False   # kept for compat with main.py health check


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_prompt(context: dict) -> str:
    return f"""You are AutoHeal AI, an expert autonomous infrastructure recovery system.
Analyze this system anomaly and provide a precise remediation plan.

System Context:
- Service: {context.get('service', 'unknown')}
- Status: {context.get('status', 'unknown')}
- CPU Usage: {context.get('cpu', 'N/A')}%
- Memory Usage: {context.get('memory', 'N/A')}%
- Error: {context.get('error', 'none')}
- Host: {context.get('host', 'unknown')}

Respond ONLY in this exact JSON format with no markdown fences:
{{
  "fix": "one-line shell command or action to execute",
  "explanation": "2-3 sentence root cause analysis and why this fix works",
  "severity": "critical|high|medium|low",
  "estimated_recovery_time": "e.g. 30 seconds",
  "preventive_measure": "one actionable future prevention tip"
}}"""


# ---------------------------------------------------------------------------
# Gemini REST call
# ---------------------------------------------------------------------------
def _call_gemini_rest(prompt: str) -> str:
    """POST to Gemini REST endpoint, return raw text of the first candidate."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
    }
    headers = {"Content-Type": "application/json"}
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"

    with httpx.Client(timeout=20) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # Navigate to text
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_gemini(context: dict) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    if not _HTTPX_AVAILABLE:
        raise RuntimeError("httpx not available")

    raw = _call_gemini_rest(_build_prompt(context))

    # Strip markdown fences if Gemini adds them anyway
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except Exception:
                continue
        raise ValueError("Could not parse JSON from Gemini response")

    parsed = json.loads(raw)
    return {
        "fix":                    parsed.get("fix", "Restart service"),
        "explanation":            parsed.get("explanation", "AI-generated fix."),
        "severity":               parsed.get("severity", "high"),
        "estimated_recovery_time": parsed.get("estimated_recovery_time", "unknown"),
        "preventive_measure":     parsed.get("preventive_measure", "Monitor regularly."),
        "source": "gemini",
    }


# ---------------------------------------------------------------------------
# Intelligent rule-based fallback (6 categories)
# ---------------------------------------------------------------------------
def _rule_based_fallback(context: dict) -> dict:
    service = context.get("service", "service")
    error   = str(context.get("error", "")).lower()
    cpu     = int(context.get("cpu",    0) or 0)
    memory  = int(context.get("memory", 0) or 0)

    if "kernel" in error or "panic" in error:
        fix = f"sudo dmesg | tail -50 && systemctl restart {service}"
        explanation = (
            "Kernel panic indicates a critical hardware or driver-level failure. "
            "Collecting kernel logs and restarting the service is the safest immediate action. "
            "Full root cause requires kernel dump analysis."
        )
        preventive = "Enable kdump for kernel crash dump collection and set up automated kernel log alerts."
        sev = "critical"

    elif "out of memory" in error or "oom" in error or memory > 90:
        fix = f"sync && echo 3 > /proc/sys/vm/drop_caches && systemctl restart {service}"
        explanation = (
            "Memory exhaustion caused the service to fail. "
            "Dropping page cache frees immediate memory before restarting the service. "
            "Investigate memory leak patterns in the application."
        )
        preventive = "Configure memory limits via cgroups and set up OOM killer alerts with automated restarts."
        sev = "critical" if memory > 95 else "high"

    elif "connection refused" in error or "timeout" in error or "unreachable" in error:
        fix = f"systemctl restart {service} && sleep 5 && curl -sf http://localhost/health"
        explanation = (
            "Service is refusing connections due to a crash or network misconfiguration. "
            "Restarting restores the listener; the health check confirms recovery. "
            "Check firewall rules if the issue persists."
        )
        preventive = "Implement circuit breaker pattern and exponential backoff for downstream calls."
        sev = "high"

    elif "disk full" in error or "no space" in error:
        fix = f"df -h && find /var/log -type f -mtime +7 -delete && systemctl restart {service}"
        explanation = (
            "Disk exhaustion prevents writes, causing service failure. "
            "Removing old logs frees space quickly; restarting ensures the service re-opens file handles. "
            "Long-term fix requires log rotation policies."
        )
        preventive = "Set up log rotation (logrotate), disk usage alerts at 80% threshold, and offload logs to S3."
        sev = "high"

    elif "certificate" in error or "ssl" in error or "tls" in error:
        fix = f"certbot renew --force-renewal && systemctl reload {service}"
        explanation = (
            "TLS/SSL certificate has expired or is misconfigured, blocking all secure connections. "
            "Force-renewing the certificate and reloading the service resolves the issue without downtime. "
            "Verify SAN entries match the configured domains."
        )
        preventive = "Automate certificate renewal with a certbot cron job and alert 30 days before expiry."
        sev = "high"

    elif "queue" in error or "consumer lag" in error or "broker" in error:
        fix = f"systemctl restart {service} && rabbitmqctl purge_queue deadletter"
        explanation = (
            "Message queue overflow or broker failure is causing consumer lag. "
            "Restarting the consumer and purging the dead-letter queue restores throughput. "
            "Analyse message processing latency for a permanent fix."
        )
        preventive = "Implement backpressure mechanisms, set queue depth alerts, and auto-scale consumers."
        sev = "high"

    elif cpu > 90:
        fix = f"renice -n 10 $(pgrep -f {service}) && sleep 10 && systemctl restart {service}"
        explanation = (
            "CPU is saturated, causing service degradation. "
            "Re-nicing the process reduces its CPU priority to allow system recovery, followed by a clean restart. "
            "Profile the service for CPU-intensive operations."
        )
        preventive = "Set CPU quotas via cgroups, implement rate limiting, and configure horizontal auto-scaling."
        sev = "high" if cpu < 95 else "critical"

    else:
        fix = f"systemctl restart {service} && journalctl -u {service} -n 100 --no-pager"
        explanation = (
            "An unclassified anomaly has been detected in the service. "
            "Restarting is the safest immediate recovery action. "
            "Review recent logs to identify the root cause."
        )
        preventive = "Add structured logging with correlation IDs and integrate with an APM tool."
        sev = "medium"

    return {
        "fix":                    fix,
        "explanation":            explanation,
        "severity":               sev,
        "estimated_recovery_time": "30–90 seconds",
        "preventive_measure":     preventive,
        "source":                 "rule_engine",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def call_ai(context: dict) -> dict:
    """
    Try Gemini REST API first; fall back to rule engine on any failure.
    Returns: fix, explanation, severity, estimated_recovery_time,
             preventive_measure, source.
    """
    if GEMINI_API_KEY and _HTTPX_AVAILABLE:
        try:
            result = _call_gemini(context)
            logger.info("[AI] Gemini response received successfully.")
            result["fix"] = f"AI Suggestion: {result['fix']}"
            return result
        except Exception as exc:
            logger.warning("[AI] Gemini call failed (%s) – using rule engine.", exc)

    result = _rule_based_fallback(context)
    logger.info("[AI] Rule-based fallback used (source=%s).", result["source"])
    result["fix"] = f"AI Suggestion: {result['fix']}"
    return result


def call_ai_freeform(prompt: str) -> str:
    """
    Free-form Gemini call for the /ai/analyze chat endpoint.
    Returns plain text (may contain markdown).
    """
    if GEMINI_API_KEY and _HTTPX_AVAILABLE:
        try:
            system = (
                "You are AutoHeal AI, a senior DevOps and SRE expert. "
                "Answer infrastructure and system reliability questions clearly and concisely. "
                "Format using markdown when helpful."
            )
            raw = _call_gemini_rest(f"{system}\n\nUser: {prompt}")
            logger.info("[AI] Gemini freeform response received.")
            return raw
        except Exception as exc:
            logger.warning("[AI] Freeform Gemini call failed: %s", exc)
            return (
                f"⚠️ **Gemini API error:** {exc}\n\n"
                "Please check your API key and network connectivity."
            )

    return (
        "⚠️ **Gemini API key not configured.**\n\n"
        "Set the `GEMINI_API_KEY` environment variable to enable live AI responses.\n\n"
        f"**Your question:** {prompt}\n\n"
        "**Demo answer:** In a live deployment I would analyse your infrastructure logs, "
        "identify the root cause using pattern matching and LLM reasoning, "
        "then provide a step-by-step remediation plan with preventive measures."
    )