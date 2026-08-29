# MerchantGPT

An autonomous AI growth manager for e-commerce merchants. MerchantGPT analyzes sales, customers, abandoned carts, and refunds, then recommends and executes growth actions: revenue leak detection, cart recovery, customer segmentation, churn prediction, marketing campaign copy, and weekly executive reports -- all queryable through an AI chat agent with tool calling over your live data.

## Features

1. **AI chat with memory** -- Claude-powered chat agent with tool calling into live SQL data, plus long-term semantic memory via pgvector.
2. **Merchant analytics dashboard** -- revenue, orders, AOV, refunds, active customers, cart abandonment, revenue trend, top products.
3. **Revenue leak detection** -- rule-based detectors for high-refund products, thin/negative margins, cart abandonment, and month-over-month decline.
4. **Abandoned cart recovery generator** -- deterministic, discount-tiered recovery message templates, optionally polished by Claude.
5. **Customer segmentation** -- RFM (Recency/Frequency/Monetary) segmentation computed relative to your own customer population.
6. **Churn prediction** -- heuristic risk scoring based on how overdue a customer is against their own historical order cadence.
7. **Marketing campaign generator** -- cart recovery, win-back, and segment-promo campaign copy.
8. **Weekly executive AI report** -- narrative summary of performance and top issues, with a deterministic fallback if no AI key is configured.
9. **Tool calling over SQL data** -- the chat agent can call `get_dashboard_summary`, `get_revenue_leaks`, `get_customer_segments`, `get_churn_risks`, and `get_abandoned_carts` as read-only tools.
10. **Responsive UI** -- Next.js 15 + Tailwind + shadcn-style components, with charts via Recharts.

Every AI-touching feature (chat, campaign copy, weekly narrative) has a deterministic non-AI fallback and works with **zero `ANTHROPIC_API_KEY`** -- only the conversational chat itself is unavailable without one; everything else keeps working.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS v4, hand-rolled shadcn-style components, Recharts |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Database | PostgreSQL + pgvector (chat memory embeddings) |
| AI | Anthropic Claude, Messages API tool-calling loop |
| Auth | JWT (python-jose) + bcrypt |
| Testing | pytest / pytest-asyncio (backend pure-logic unit tests) |
| Deployment | Docker Compose (local/self-hosted), Vercel (frontend) + any container host (backend) |

## Project structure

```
merchantgpt/
├── backend/
│   ├── app/
│   │   ├── agent/           # Claude tool-calling loop + tool schemas
│   │   ├── api/routes/      # auth, analytics, chat, campaigns/reports
│   │   ├── core/            # config, security (JWT + bcrypt)
│   │   ├── db/              # SQLAlchemy base + async session
│   │   ├── models/          # ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # segmentation, churn, revenue leaks, cart
│   │   │                    # recovery, embeddings, analytics, chat,
│   │   │                    # campaign copy, weekly reports
│   │   └── tests/           # unit tests for pure business logic
│   ├── scripts/seed.py      # idempotent realistic demo-data seeder
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # App Router pages (login, register, dashboard, ...)
│   │   ├── components/       # UI primitives + feature components
│   │   └── lib/               # typed API client, auth context, hooks
│   └── Dockerfile
├── docs/                     # architecture, API reference, deployment guide
└── docker-compose.yml
```

## Quick start (Docker Compose)

```bash
cp backend/.env.example backend/.env       # edit JWT_SECRET, optional ANTHROPIC_API_KEY
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs at `/docs`)
- Postgres (with pgvector): `localhost:5432`

Then seed realistic demo data:

```bash
docker compose exec backend python -m scripts.seed
```

Demo login: `demo@aurorahome.example` / `Demo@12345`.

> Docker Compose files are provided and follow standard multi-stage build practices, but could not be build-tested in this environment (Docker was not installed on the machine this project was built on). The backend and frontend were both fully verified by running them directly (see below) against the same Dockerfile dependency versions.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL / DATABASE_URL_SYNC to a local Postgres with pgvector enabled
python -m scripts.seed
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL to the backend URL
npm run dev
```

## Environment variables

See [`backend/.env.example`](backend/.env.example) and [`frontend/.env.example`](frontend/.env.example) for the full list. Notably:

- `ANTHROPIC_API_KEY` is **optional**. Without it, the chat endpoint returns a clear "not configured" message instead of crashing, and campaign/report generation silently falls back to deterministic templates.
- `CREATE EXTENSION vector` is attempted on startup but failure is caught and logged rather than crashing the app -- most managed Postgres hosts (Render, Supabase, Neon, RDS) require an admin to enable extensions once via their dashboard, since the application's own database role typically cannot run `CREATE EXTENSION` itself.

## Documentation

- [Architecture](docs/architecture.md)
- [API reference](docs/api-reference.md)
- [Deployment guide](docs/deployment.md)
