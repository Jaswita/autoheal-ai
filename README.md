#  AutoHeal AI – Multi-Agent Autonomous Workflow Recovery System

> **Hackathon Project** · Agentic AI for Autonomous Enterprise Workflows

AutoHeal AI is a production-grade prototype where **five specialised AI agents** collaborate to detect, diagnose, fix, and audit system failures — fully autonomously.

---

##  Architecture

```
Monitor Agent → Decision Agent → Execution Agent → Verification Agent → Audit Agent
```

| Agent | Role |
|---|---|
| **Monitor** | Reads logs, detects CPU/memory spikes and service outages |
| **Decision** | Classifies issue type and severity (high / medium / low) |
| **Execution** | Applies rule-based playbook fix **or** calls Gemini AI for unknown issues |
| **Verification** | Simulates post-fix health checks and reports recovery status |
| **Audit** | Persists every pipeline run to `data/audit_trail.json` |

---

##  Quick Start

### 1 – Clone & enter project
```bash
cd autoheal-ai
```

### 2 – Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
```

### 3 – Install dependencies
```bash
pip install -r requirements.txt
```

### 4 – (Optional) Set Gemini API key
```bash
set GEMINI_API_KEY=your_key_here   # Windows
# export GEMINI_API_KEY=...        # macOS/Linux
```
Without the key the system falls back to an intelligent rule-based fix engine.

### 5 – Run the server
```bash
uvicorn main:app --reload
```

### 6 – Open in browser
| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Live dashboard |
| `http://127.0.0.1:8000/docs` | Swagger auto-docs |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/run` | Run pipeline on a fresh simulated log |
| `GET` | `/run?scenario=service_down` | Force a specific scenario |
| `GET` | `/run?scenario=high_cpu` | Force high CPU scenario |
| `GET` | `/run?scenario=high_memory` | Force high memory scenario |
| `GET` | `/run?scenario=healthy` | Force healthy system |
| `POST` | `/run/custom` | Run with your own JSON log body |
| `GET` | `/run/batch?count=5` | Run N pipelines in one shot |
| `GET` | `/run/file` | Process all logs from `data/logs.json` |
| `GET` | `/audit` | Retrieve audit trail |
| `DELETE` | `/audit` | Clear audit trail |
| `GET` | `/health` | Liveness check |
| `GET` | `/docs` | Interactive Swagger UI |

---

##  Project Structure

```
autoheal-ai/
├── main.py                   # FastAPI application + pipeline orchestration
├── agents/
│   ├── monitor_agent.py      # Anomaly detection
│   ├── decision_agent.py     # Issue classification & severity
│   ├── execution_agent.py    # Playbook + AI fix execution
│   ├── verification_agent.py # Post-fix health verification
│   └── audit_agent.py        # Audit trail persistence
├── utils/
│   ├── log_simulator.py      # Scenario-based log generator
│   └── ai_helper.py          # Gemini API integration + fallback
├── data/
│   ├── logs.json             # Sample log entries
│   └── audit_trail.json      # Auto-generated audit trail
├── frontend/
│   └── index.html            # Premium dark-mode dashboard
├── requirements.txt
└── README.md
```

---

##  AI Integration

- **Primary**: Google Gemini 1.5 Flash (free tier) via `google-generativeai` SDK
- **Fallback**: Rule-based remediation engine covering 15+ common error patterns
- Set `GEMINI_API_KEY` environment variable to enable AI-powered fixes

---

##  Expected API Response

```json
{
  "run_id": "uuid",
  "log": { "service": "nginx", "status": "down", "cpu": 45, ... },
  "monitor": { "anomaly_detected": true, "anomalies": ["service_down:nginx"] },
  "decision": { "issue": "nginx_down", "severity": "high", "action_required": true },
  "execution": { "action_taken": "systemctl restart nginx", "source": "playbook" },
  "verification": { "status": "success", "resolved": true, "checks": [...] },
  "audit_entry": { "run_id": "...", "timestamp": "...", ... }
}
```

---

##  Tech Stack

- **Backend**: Python 3.11+ · FastAPI · Uvicorn
- **AI**: Google Gemini 1.5 Flash
- **Frontend**: Pure HTML · Vanilla CSS · Vanilla JS (no framework)
- **Storage**: JSON files (no database required)

---

*Built for Hackathon 2026 – Agentic AI for Autonomous Enterprise Workflows*
