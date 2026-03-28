# 🤖 AutoHeal AI – Autonomous Workflow Recovery System

> **Hackathon 2026** · Multi-Agent Agentic AI · Powered by Google Gemini 1.5 Flash

AutoHeal AI is a **production-grade autonomous incident response system** where five specialised AI agents collaborate to detect, diagnose, remediate, verify, and audit system failures — fully autonomously and in real time.

---

## 🆕 What's New (v2.0) — Hackathon Differentiators

| Feature | Description |
|---|---|
| 🧠 **Real Gemini API** | `utils/ai_helper.py` now calls **Google Gemini 1.5 Flash** for unknown/novel failures — not simulated |
| 💬 **AI Chat Interface** | Dedicated `/ai/analyze` endpoint + dashboard chat UI — ask anything about infrastructure |
| ⚙️ **Smart Rule Engine Fallback** | 6 deep rule categories kick in when Gemini is unavailable (no API key? still works) |
| 📊 **Live Stats API** | `/stats` endpoint tracks total runs, AI fix rate, resolution rate, Gemini call count |
| 🔍 **Richer Verification** | 5-check post-fix health suite with per-check detail and confidence scoring |
| 🛡️ **Preventive Measures** | Every AI fix includes a future-prevention tip surfaced on the dashboard |
| 🎨 **3-Page Dashboard** | Dashboard · AI Chat · Audit Trail — dark-mode premium UI with animations |
| 🏷️ **AI Source Badges** | UI distinguishes Gemini vs Rule Engine vs Playbook fixes at a glance |

---

## 🏗 Architecture

```
Log Input
   │
   ▼
Monitor Agent  ──→  Decision Agent  ──→  Execution Agent  ──→  Verification Agent  ──→  Audit Agent
(detect anomaly)   (classify severity)  (playbook OR AI fix)   (5-check health suite)  (persist trail)
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                             Gemini 1.5 Flash    Rule Engine
                             (live API call)     (6 categories)
```

### Agent Responsibilities

| Agent | Role |
|---|---|
| **Monitor** | Detects CPU spikes, memory exhaustion, service outages, and error fields in logs |
| **Decision** | Classifies issue type and severity (critical / high / medium / low) |
| **Execution** | Runs playbook command, or calls **Gemini AI** for unknown issues |
| **Verification** | Runs 5 post-fix health checks; computes confidence score per fix source |
| **Audit** | Persists every run to `data/audit_trail.json` — full lineage preserved |

---

## 🚀 Quick Start

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

### 4 – Set Gemini API key *(enables real AI)*
```bash
# Windows
set GEMINI_API_KEY=your_key_here

# macOS / Linux
export GEMINI_API_KEY=your_key_here
```
> 🔑 Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).  
> Without a key, the system uses the intelligent **rule-based engine** — all features still work.

### 5 – Run the server
```bash
uvicorn main:app --reload
```

### 6 – Open in browser
| URL | Description |
|---|---|
| `http://127.0.0.1:8000/` | Live dashboard |
| `http://127.0.0.1:8000/docs` | Swagger auto-docs |
| `http://127.0.0.1:8000/health` | AI mode status |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/run` | Run pipeline on a random simulated log |
| `GET` | `/run?scenario=service_down` | Force service-down scenario |
| `GET` | `/run?scenario=high_cpu` | Force high CPU scenario |
| `GET` | `/run?scenario=high_memory` | Force high memory scenario |
| `GET` | `/run?scenario=healthy` | Force healthy system |
| `GET` | `/run?scenario=unknown` | Force AI-handled unknown issue |
| `POST` | `/run/custom` | Run with your own JSON log body |
| `GET` | `/run/batch?count=5` | Run N pipelines in one shot |
| `GET` | `/run/file` | Process all logs from `data/logs.json` |
| `POST` | `/ai/analyze` | **NEW** – Free-form Gemini AI chat |
| `GET` | `/stats` | **NEW** – Live run statistics |
| `GET` | `/audit` | Retrieve audit trail |
| `DELETE` | `/audit` | Clear audit trail and stats |
| `GET` | `/health` | Liveness check + AI mode info |
| `GET` | `/docs` | Interactive Swagger UI |

---

## 🧠 AI Integration (v2.0)

### Real Gemini API Call
When `GEMINI_API_KEY` is set and `google-generativeai` is installed:
- `execution_agent.py` calls `call_ai()` → `call_ai_freeform()` in `utils/ai_helper.py`
- A structured prompt is sent to **Gemini 1.5 Flash**
- Response is parsed and returns: `fix`, `explanation`, `severity`, `estimated_recovery_time`, `preventive_measure`
- The `/ai/analyze` POST endpoint lets users chat with Gemini directly

### Intelligent Rule-Engine Fallback
Six deep rule categories when Gemini is unavailable:
1. Kernel panic / system crash
2. OOM / memory exhaustion
3. Connection refused / timeout / unreachable
4. Disk full / no space left
5. TLS / SSL / certificate errors
6. Message queue / broker failures

Each rule returns the same structured response as Gemini — the frontend cannot tell the difference.

---

## 📊 Example API Responses

### `/run?scenario=unknown` (AI-powered)
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "execution": {
    "action_taken": "AI Suggestion: sudo dmesg | tail -50 && systemctl restart nginx",
    "source": "gemini",
    "fix_detail": "Kernel panic indicates a critical hardware or driver-level failure...",
    "preventive_measure": "Enable kdump for kernel crash dump collection.",
    "severity": "critical",
    "estimated_recovery_time": "60-120 seconds"
  },
  "verification": {
    "status": "success",
    "resolved": true,
    "confidence": 88,
    "checks": [
      {"name": "Service Health Probe", "passed": true, "detail": "HTTP 200 OK"},
      {"name": "CPU Utilisation", "passed": true, "detail": "CPU at 34%"},
      {"name": "Memory Utilisation", "passed": true, "detail": "Memory at 45%"},
      {"name": "Error Log Clearance", "passed": true, "detail": "No new errors in last 60s"},
      {"name": "Network Connectivity", "passed": true, "detail": "Downstream services reachable"}
    ]
  }
}
```

### `/ai/analyze` (Chat endpoint)
```bash
curl -X POST http://localhost:8000/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Why does Redis run out of memory and how do I fix it?"}'
```

---

## 📦 Project Structure

```
autoheal-ai/
├── main.py                     # FastAPI app + pipeline + /stats + /ai/analyze
├── agents/
│   ├── monitor_agent.py        # Anomaly detection (CPU/memory/status/error)
│   ├── decision_agent.py       # Issue classification & severity scoring
│   ├── execution_agent.py      # Playbook + Gemini AI execution
│   ├── verification_agent.py   # 5-check post-fix health verification
│   └── audit_agent.py          # Persistent audit trail (JSON)
├── utils/
│   ├── log_simulator.py        # Scenario-based log generator
│   └── ai_helper.py            # ★ Real Gemini API + rule-engine fallback
├── data/
│   ├── logs.json               # Sample log entries
│   └── audit_trail.json        # Auto-generated (gitignored)
├── frontend/
│   └── index.html              # ★ 3-page premium dark-mode dashboard
├── requirements.txt
└── README.md
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+ · FastAPI · Uvicorn |
| **AI (Primary)** | Google Gemini 1.5 Flash (`google-generativeai` SDK) |
| **AI (Fallback)** | Custom rule-engine (6 categories, deterministic) |
| **Frontend** | Pure HTML + Vanilla CSS + Vanilla JS (zero dependencies) |
| **Storage** | JSON files (no database required) |

---

## 🔬 Unique Features for Judges

1. **Dual AI Brain** — Real Gemini API with intelligent fallback means the system *always* works, even offline
2. **Structured AI Prompting** — Gemini is instructed to return strict JSON with fix, explanation, severity, recovery time, and prevention tip
3. **AI Chat Panel** — Live Q&A with Gemini through the dashboard, not just automated fixes
4. **Source Transparency** — Every fix is labelled (🧠 Gemini / ⚙️ Rule Engine / 📋 Playbook) — full explainability
5. **5-Dimensional Verification** — Service probe, CPU, memory, log clearance, and network checks after every fix
6. **Live Stats** — Real-time resolution rate, AI fix ratio, and Gemini call counter

---

*Built for Hackathon 2026 – Agentic AI for Autonomous Enterprise Workflows*
