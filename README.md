# Deployment Safety Advisor

AI-powered deployment safety evaluation agent built with GPT-4o-mini 
and tool calling. Evaluates deployment requests against live alert 
states, change freeze windows, and deployment history before returning 
a structured go/no-go verdict.

## Architecture
POST /evaluate-deployment
↓
FastAPI receives request
↓
GPT-4o-mini agent reasons about the deployment
↓
Agent calls 3 tools autonomously:
├── check_active_alerts(service_id)
├── check_change_freeze(region)
└── get_recent_deployments(service_id)
↓
Synthesises verdict across all evidence
↓
Returns structured JSON: verdict, risk_score, reasons, actions

## Example

Input:
```json
{
  "service_id": "svc-payments",
  "service_name": "payments-service",
  "version": "v2.2.0",
  "target_region": "ap-mumbai-1",
  "deployed_by": "muthu"
}
```

Output:
```json
{
  "verdict": "NO_GO",
  "risk_score": 85,
  "safe_to_deploy": false,
  "reasons": [
    "Active CPU_HIGH alert on payments-service",
    "Change freeze active in ap-mumbai-1 — quarter-end freeze",
    "Most recent deployment v2.1.0 failed"
  ],
  "recommended_actions": [
    "Resolve active CPU alert before deploying",
    "Wait for change freeze window to end",
    "Review failure root cause from v2.1.0"
  ]
}
```

## Design decisions

**Why tool calling over a single prompt?**
Single prompt approach requires stuffing all context upfront. 
Tool calling lets the agent decide what information it needs 
and fetch it dynamically — mirrors how a human engineer 
would investigate before approving a deployment.

**Why Pydantic for output?**
LLM outputs are non-deterministic. Pydantic enforces schema 
on every response — if the model hallucinates a field or 
returns wrong types, it fails loudly rather than silently 
corrupting downstream systems.

**Why SQLite for mock data?**
Zero infrastructure overhead. The same pattern works with 
any database behind the tool functions — swap SQLite for 
Postgres or Oracle DB without changing agent logic.

## Setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
OPENAI_API_KEY=your_key_here

Seed database:
```powershell
python seed_db.py
```

Run:
```powershell
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` to test interactively.

## Background

This project extends the alert-aware deployment control framework 
I designed at Oracle Cloud Infrastructure — a platform governing 
deployments across 120+ OCI regions using Kafka-driven event 
processing and distributed locking. This agent adds an LLM reasoning 
layer that explains safety decisions in plain English and generates 
specific remediation guidance.

## Tech stack

Python · FastAPI · OpenAI GPT-4o-mini · Pydantic · SQLite · uvicorn