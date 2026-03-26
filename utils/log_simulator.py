"""
Log Simulator – generates random or scenario-based system logs.
"""
import random
import datetime
import json
import os

SERVICES = ["nginx", "api-gateway", "database", "redis", "worker", "auth-service", "message-queue"]
HOSTS = ["prod-server-01", "prod-server-02", "prod-db-01", "prod-cache-01", "prod-worker-01"]

ERRORS = {
    "nginx": ["connection refused", "502 bad gateway", "upstream timeout"],
    "api-gateway": ["rate limit exceeded", "upstream unreachable", "ssl handshake failed"],
    "database": ["out of memory", "too many connections", "disk full"],
    "redis": ["connection timeout", "max clients reached", "eviction policy triggered"],
    "worker": ["timeout exceeded", "segmentation fault", "queue overflow"],
    "auth-service": ["token validation failed", "ldap unreachable", "certificate expired"],
    "message-queue": ["broker unavailable", "consumer lag critical", "partition leader election"],
}


def generate_log(force_anomaly=False, service=None, scenario=None):
    svc = service or random.choice(SERVICES)
    host = random.choice(HOSTS)
    ts = datetime.datetime.utcnow().isoformat()

    if scenario == "healthy":
        return _healthy_log(svc, host, ts)
    if scenario == "high_cpu":
        return _high_cpu_log(svc, host, ts)
    if scenario == "high_memory":
        return _high_memory_log(svc, host, ts)
    if scenario == "service_down":
        return _service_down_log(svc, host, ts)
    if scenario == "unknown":
        return _unknown_issue_log(svc, host, ts)

    # Random behavior
    cpu = random.randint(5, 95)
    memory = random.randint(10, 95)
    is_down = random.random() < 0.15

    return {
        "id": f"log_{random.randint(1000, 9999)}",
        "timestamp": ts,
        "service": svc,
        "status": "down" if is_down else "running",
        "cpu": cpu,
        "memory": memory,
        "error": random.choice(ERRORS[svc]) if is_down else None,
        "host": host,
    }


def _healthy_log(svc, host, ts):
    return {
        "id": f"log_{random.randint(1000, 9999)}",
        "timestamp": ts,
        "service": svc,
        "status": "running",
        "cpu": random.randint(5, 50),
        "memory": random.randint(10, 60),
        "error": None,
        "host": host,
    }


def _high_cpu_log(svc, host, ts):
    return {
        "id": f"log_{random.randint(1000, 9999)}",
        "timestamp": ts,
        "service": svc,
        "status": "running",
        "cpu": random.randint(91, 100),
        "memory": random.randint(40, 80),
        "error": None,
        "host": host,
    }


def _high_memory_log(svc, host, ts):
    return {
        "id": f"log_{random.randint(1000, 9999)}",
        "timestamp": ts,
        "service": svc,
        "status": "running",
        "cpu": random.randint(20, 60),
        "memory": random.randint(91, 100),
        "error": None,
        "host": host,
    }


def _service_down_log(svc, host, ts):
    return {
        "id": f"log_{random.randint(1000, 9999)}",
        "timestamp": ts,
        "service": svc,
        "status": "down",
        "cpu": random.randint(10, 60),
        "memory": random.randint(10, 70),
        "error": random.choice(ERRORS[svc]),
        "host": host,
    }


def _unknown_issue_log(svc, host, ts):
    return {
        "id": f"log_{random.randint(1000, 9999)}",
        "timestamp": ts,
        "service": svc,
        "status": "error",
        "cpu": random.randint(40, 70),
        "memory": random.randint(40, 70),
        "error": "unexpected kernel panic in module xyz",
        "host": host,
    }


def load_logs_from_file(path=None):
    if path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "data", "logs.json")
    with open(path, "r") as f:
        return json.load(f)