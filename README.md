# SupportOps

A synthetic technical-support investigation sandbox. The planned agent will inspect
subscription records and logs, cite evidence, propose a specific action, and verify
the result after human approval.

## Current foundation

- React + TypeScript + Vite review workspace with live API/database status.
- FastAPI liveness, database readiness, and public configuration endpoints.
- Postgres via Docker Compose; SQLAlchemy connection foundation.
- PydanticAI model adapter for a configurable OpenAI-compatible open-model endpoint.
- Alembic schema for plans, customers, subscriptions, payments, event logs and support
  tickets, plus deterministic synthetic seed records.
- Backend smoke and seed tests. No investigation loop or mutation endpoints exist yet.

## Run locally

Prerequisites: Node.js 22 LTS, Python 3.11+, uv, Docker Desktop.
The development interpreter is pinned to Python 3.12 via `.python-version`.
Run commands from the indicated directories. Docker Desktop must be running.

From the repository root:

```powershell
docker compose up -d postgres
```

In a backend terminal:

```powershell
cd backend
Copy-Item .env.example .env
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a separate frontend terminal:

```powershell
cd frontend
npm install
npm run dev
```

`app.seed` truncates the support tables and reloads the same rows, so rerun it to reset
the sandbox. The first scenario is ticket `tkt_5002`: a customer who paid for Pro but
whose account still shows Free.

Open http://localhost:5173. API docs: http://localhost:8000/docs.
The frontend development proxy forwards `/api` to FastAPI.
For a production deployment, configure the same reverse-proxy route; Vite preview
does not provide the development API proxy.

## Open model configuration

The adapter defaults to Ollama at `http://localhost:11434/v1`, model `qwen3:8b`.
An installed model is not required to run the foundation. When ready, install Ollama
and run `ollama pull qwen3:8b` (a substantial download; hardware requirements vary).
Set `MODEL_BASE_URL`, `MODEL_NAME`, and `MODEL_API_KEY` in `backend/.env` to use
another compatible endpoint. Credentials stay on the backend.

Tool-call and timeout settings are configuration only until the runtime is built.
An API health check does not test model connectivity.

## Checks

```powershell
cd backend
uv run pytest
uv run ruff check .
```

```powershell
cd frontend
npm run build
```

## Next milestone

1. ~~Add migrations and deterministic customer/subscription/payment/event seed records.~~
   Done; seeds cover the first scenario so far.
2. Implement narrow read-only tools and five development scenarios.
3. Add a bounded investigation loop and persist evidence/trace events.
4. Implement exact-action approval, idempotent replay, and post-action verification.
5. Evaluate against a scripted baseline; keep held-out answer keys outside agent access.

This is a local development environment, not a production service. Default database
credentials are for the local sandbox only. No real customer data is included.
