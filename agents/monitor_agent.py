"""
Monitor Agent – reads logs and detects anomalies.

Anomaly rules:
  • CPU  > 90 %
  • Memory > 90 %
  • service status == "down"
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

CPU_THRESHOLD = 90
MEMORY_THRESHOLD = 90


class MonitorAgent:
    """Scans a log entry and reports whether it contains anomalies."""

    def __init__(self, cpu_threshold: int = CPU_THRESHOLD, memory_threshold: int = MEMORY_THRESHOLD):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def analyze(self, log: dict) -> dict:
        """
        Analyze a single log entry.

        Returns:
            {
                "anomaly_detected": bool,
                "anomalies": list[str],
                "log": dict
            }
        """
        anomalies = []

        # Service down check
        if str(log.get("status", "")).lower() == "down":
            anomalies.append(f"service_down:{log.get('service', 'unknown')}")

        # High CPU check
        try:
            cpu = int(log.get("cpu", 0))
            if cpu > self.cpu_threshold:
                anomalies.append(f"high_cpu:{cpu}%")
        except (TypeError, ValueError):
            pass

        # High memory check
        try:
            mem = int(log.get("memory", 0))
            if mem > self.memory_threshold:
                anomalies.append(f"high_memory:{mem}%")
        except (TypeError, ValueError):
            pass

        # Error field present
        error = log.get("error")
        if error:
            anomalies.append(f"error_reported:{error}")

        detected = len(anomalies) > 0
        if detected:
            logger.info("[MonitorAgent] Anomalies detected: %s", anomalies)
        else:
            logger.info("[MonitorAgent] Log is healthy.")

        return {
            "anomaly_detected": detected,
            "anomalies": anomalies,
            "log": log,
        }
