# AI Agent System v2.3.2

A full-stack AI assistant platform with:
- **FastAPI backend** for sessions, chat, memory, document search, web search, and orchestration.
- **Next.js frontend** for multi-session chat UI.
- **Persistent memory** (conversation + extracted facts) with quality gates.
- **Intelligent orchestrator** with strategy selection, cache, retries, rate limiting, and analytics.

---

## Project Overview

This repository contains two main applications:

1. **Backend API** (`app/`)
   - FastAPI service with async SQLAlchemy.
   - Multi-agent routing and enhanced chat workflows.
   - Memory and fact management endpoints.
   - Intelligent query orchestration (`/api/v1/orchestrate`).

2. **Frontend UI** (`ui/ai-agent-ui/`)
   - Next.js (App Router) + React + TypeScript.
   - Session list, chat area, context panel, and theming.
   - Client-side state with Zustand and server-state with React Query.

---

## Core Features

- **Session-based chat** with message history.
- **Enhanced chat pipeline** that can combine memory, documents, and web results.
- **Fact extraction + memory write controls** (`MemoryWriteGate`, TTL policy, auditing helpers).
- **Document indexing/search** via ChromaDB + sentence-transformers.
- **Web search integration** for fresh external context.
- **Orchestrator subsystem** with:
  - query analysis,
  - memory coverage evaluation,
  - decision engine,
  - response cache,
  - retry handler,
  - circuit breaker,
  - rate limiter,
  - formatting/metrics/feedback modules.
- **Six production AI models**: mistral, deepseek, llama3, groq,
  medical, gpt-oss — routed automatically by the decision engine.
- **Fact extraction**: Automatically extracts and persists facts
  from conversations via FactExtractor (requires Ollama running
  locally with at least one model available).

---

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- SQLite (default via `aiosqlite`)
- ChromaDB + sentence-transformers
- DuckDuckGo Search
- Pydantic v2
- Pytest

### Frontend
- Next.js 16
- React 19
- TypeScript 5
- Tailwind CSS 4
- Zustand
- TanStack React Query
- Vitest + Testing Library

---

## Repository Structure

```text
ai_agent_v2/
├── app/
│   ├── api/                 # FastAPI routes + dependencies
│   ├── core/                # config, db, security config
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # business logic
│   │   └── orchestrator/    # intelligent orchestration components
│   └── main.py              # FastAPI entrypoint
├── tests/                   # unit/integration/api tests
├── security/                # input validation and security helpers
├── scripts/                 # utility scripts (db migration/init/dedup)
├── documentation/           # API, deployment, user docs, reports
└── ui/ai-agent-ui/          # Next.js frontend app
```

---

## Quick Start

## 1) Backend

```bash
# from repository root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# optional: copy and edit env
cp .env.example .env

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API base URL: `http://localhost:8000/api/v1`

Interactive docs:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 2) Frontend

```bash
cd ui/ai-agent-ui
npm install

echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

UI URL: `http://localhost:3000`

---

## Production Deployment

The system runs in two isolated environments on the same machine:

| Environment | Directory | Backend Port | Frontend Port | Service |
|-------------|-----------|-------------|---------------|---------|
| Production  | `/srv/ai_agent` | 8000 | 3000 | `ai-agent.service` |
| Development | `/srv/ai_agent_dev_git` | 8001 | 3001 | `ai-agent-dev.service` |

### Post-Deployment Smoke Check (Mandatory)
After every production deployment, run the smoke suite to verify
the live server is healthy:
```bash
cd /srv/ai_agent_dev_git
./venv/bin/python -m pytest tests/e2e/test_smoke.py -v
# Expected: 4 passed
```

### Deployment Principle
> "If you can't curl it, it doesn't work."
> Unit tests passing is necessary but not sufficient.
> Always verify with a real HTTP request after deployment.

---

## Key API Endpoints

### System
- `GET /api/v1/health`
- `GET /api/v1/system/cache-stats`

### Sessions
- `POST /api/v1/sessions`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `PATCH /api/v1/sessions/{session_id}`
- `DELETE /api/v1/sessions/{session_id}`
- `GET /api/v1/sessions/{session_id}/messages`
- `GET /api/v1/sessions/{session_id}/facts`

### Chat / Orchestration
- `POST /api/v1/chat/enhanced`
- `POST /api/v1/orchestrate`

### Agents
- `GET /api/v1/agents/status`
- `POST /api/v1/agents/select`

### Documents / Search
- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/search`
- `POST /api/v1/search/web`

### Memory
- `POST /api/v1/memory/facts/search`
- `DELETE /api/v1/memory/facts/{fact_id}`
- `GET /api/v1/memory/stats`

---

## Testing

### Backend
```bash
# Activate venv first
source venv/bin/activate   # or: ./venv/bin/python -m pytest

# Run full backend test suite (961 tests)
./venv/bin/python -m pytest tests/ -v

# Run by category
./venv/bin/python -m pytest tests/unit -v
./venv/bin/python -m pytest tests/integration -v
./venv/bin/python -m pytest tests/api -v

# Run smoke tests (requires live prod server on port 8000)
./venv/bin/python -m pytest tests/e2e/test_smoke.py -v
# Note: smoke tests are skipped automatically in CI
```

### Frontend
```bash
cd ui/ai-agent-ui
npm test
```

---

## Notes

- Default DB URL is SQLite at `./data/agent.db` (configurable via env).
- Some AI providers/models require external services or API keys (e.g., Groq, Ollama).
- There is a legacy UI backup in `ui/ai-agent-ui-backup-20260114/`; active UI is `ui/ai-agent-ui/`.

---

## Architectural Notes

### Dependency Injection (deps.py)
All major services are wired in `app/api/deps.py`. If a service
exists and is tested but not producing results in production,
check that it is injected in `get_orchestrator()`. Historical
examples of this pattern:
- Orchestrator bypass (7 weeks, fixed v2.3.1)
- FactExtractor not injected (fixed v2.3.2)

### Memory Write Architecture
All fact writes must go through `MemoryWriteGate` via the
Orchestrator. Direct writes to `MemoryService` outside the
Orchestrator violate the single-owner principle.

### Thread Isolation
Facts are scoped to `session_id` / `thread_id`. Facts from
Session A are never visible in Session B queries.

---

## Related Docs

- `documentation/API.md`
- `documentation/DEPLOYMENT.md`
- `documentation/USER_GUIDE.md`
- `app/services/orchestrator/README.md`
