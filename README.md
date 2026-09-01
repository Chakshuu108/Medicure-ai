# MediCure AI Platform v3.0

Full-stack **agentic AI healthcare platform** with LangGraph multi-agent orchestration, real-time agent visualization, FastAPI backend, React frontend, and PostgreSQL.

## Architecture

```
frontend/          React + TypeScript + Vite + Tailwind
backend/           FastAPI + LangChain + LangGraph + SQLAlchemy
docker-compose.yml PostgreSQL 16
```

### Agent System (LangGraph)
- **Orchestrator** — routes requests to specialist agents
- **Conversation Agent** — context-aware chat with tool calling
- **Risk Assessment Agent** — clinical risk scoring
- **Health Evaluation Agent** — adherence & behavioral trends
- **Alerting Agent** — automated clinical alerts
- **Scheduling Agent** — OPD appointment booking
- **Health Guardian** — autonomous cross-session monitoring
- **Health Intelligence Agent** — ML risk + clinical narrative
- **Response Synthesizer** — combines agent outputs

Agent execution events stream to the frontend via **Server-Sent Events (SSE)**.

## Quick Start

### 1. Start PostgreSQL
```bash
docker compose up -d
```

### 2. Backend
```bash
cd backend
cp ../.env.example .env
# Edit .env — add your GROQ_API_KEY

pip install -r requirements.txt
python scripts/seed_demo.py
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## Demo Credentials

| Role | Login | Password |
|------|-------|----------|
| **Admin** | admin@medicure.demo | demo123 |
| **Doctor** | doctor@medicure.demo | demo123 |
| **Receptionist** | reception@medicure.demo | demo123 |
| **Patient** | PAT-DEMO-0001 | *(none)* |

## API Docs

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Tech Stack

**Backend:** FastAPI, LangChain, LangGraph, SQLAlchemy, PostgreSQL, Groq LLM, SSE  
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Framer Motion  
**Infrastructure:** Docker Compose, JWT auth, bcrypt passwords

## Resume Highlights

- Multi-agent orchestration with LangGraph state machines
- Real-time agent execution visualization (SSE)
- Tool-calling ReAct loops with dynamic routing
- Persistent agent memory & execution logs (PostgreSQL)
- Full RBAC: Admin, Doctor, Receptionist, Patient portals
- Production patterns: async DB, CORS, env config, API validation
