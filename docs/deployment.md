# Deployment guide

## Recommended split

- **Frontend** → Vercel (native Next.js support, zero config beyond the env var below).
- **Backend** → any container host with a managed Postgres add-on: Render, Railway, Fly.io, or a plain VM running the provided `backend/Dockerfile`.
- **Database** → a managed Postgres with the pgvector extension available (Supabase, Neon, Render Postgres, or self-hosted `pgvector/pgvector` image).

## 1. Database

Provision a Postgres instance and, as an admin/superuser (via the host's dashboard or `psql`), run once:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The backend also attempts this automatically on startup and will continue gracefully if it lacks permission (see [architecture.md](architecture.md)) -- but on a fresh managed database, running it once yourself avoids relying on that fallback.

## 2. Backend

Build and deploy `backend/Dockerfile` (or run `uvicorn app.main:app --host 0.0.0.0 --port $PORT` directly on a Python 3.13 host with `pip install -r requirements.txt`).

Required environment variables (see `backend/.env.example`):

| Variable | Notes |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` -- used by the running app |
| `DATABASE_URL_SYNC` | `postgresql+psycopg2://...` -- used only by `scripts/seed.py` |
| `JWT_SECRET` | Long random string. Rotate to invalidate all sessions. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list; must include your deployed frontend origin |
| `ANTHROPIC_API_KEY` | Optional -- omit to run with AI chat disabled and template-based campaigns/reports |

After first deploy, seed demo data once (optional, useful for a live demo):

```bash
python -m scripts.seed
```

`seed.py` is idempotent -- it checks for the existing demo merchant by name and skips if found, so it's safe to run more than once.

## 3. Frontend

Deploy `frontend/` to Vercel (or build `frontend/Dockerfile`). Set:

| Variable | Notes |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the deployed backend, no trailing slash, no `/api/v1` suffix |

`NEXT_PUBLIC_*` variables are baked in at build time -- if you change the backend URL, redeploy the frontend rather than only changing the runtime environment.

## 4. Docker Compose (self-hosted / local demo)

```bash
cp backend/.env.example backend/.env   # set JWT_SECRET at minimum
docker compose up --build
docker compose exec backend python -m scripts.seed
```

This brings up Postgres (with pgvector pre-installed via the `pgvector/pgvector:pg17` image), the backend on `:8000`, and the frontend on `:3000`, wired together with sane defaults. See the root `docker-compose.yml` for the exact configuration.

## Post-deploy checklist

- [ ] `GET {BACKEND_URL}/api/health` returns `{"status": "ok"}`
- [ ] `POST {BACKEND_URL}/api/v1/auth/register` succeeds and returns a token
- [ ] Frontend login page loads and can reach the backend (check browser network tab for CORS errors -- confirm `CORS_ALLOWED_ORIGINS` includes the exact deployed frontend origin)
- [ ] `python -m scripts.seed` completed without error, or you've created your own merchant via `/register`
- [ ] If using AI chat: `ANTHROPIC_API_KEY` is set on the backend and a test message returns a real Claude reply rather than the "not configured" fallback
