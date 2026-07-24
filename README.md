# AI Business Operating System (AI BOS)

AI BOS is an AI-first, modular, cloud-native platform intended to unify business operations across multiple vertical applications.

This repository is a starting point: documentation + a backend foundation (FastAPI) + a frontend shell (React) with JWT-based auth (login / refresh / me) and RBAC-style permission checks.

## Key ideas

- Not a classic ERP: AI BOS is the platform (operating system) on top of which vertical apps plug in.
- AI-first: agents and workflows are first-class concepts.
- Modular CORE: shared foundations (identity, authorization, observability, etc.) are reusable.
- Multi-tenant by design: each organization is isolated by `org_id` (future work extends this).

## Docs (source of truth)

All enterprise documentation lives in:

- `Document/INDEX.md` (main entry)

Suggested reading order:

1. `Document/README_00_Vision.md`
2. `Document/README_02_Architecture.md`
3. `Document/README_05_Core.md`
4. `Document/README_40_ImplementationRoadmap.md`

## Repo structure

Top-level:

- `Document/` - enterprise documentation (AI BOS)
- `ai-bos-backend/` - FastAPI backend (identity/RBAC/observability + minimal real endpoints)
- `ai-bos-frontend/` - React frontend shell (pages for modules)
- `apps/` - (scaffold) vertical app shells (placeholder READMEs)
- `platform/` - (scaffold) CORE modules (placeholder READMEs)
- `services/` - (scaffold) infrastructure services (placeholder READMEs)
- `packages/` - (scaffold) shared libraries (placeholder READMEs)
- `pnpm-workspace.yaml`, `turbo.json` - monorepo tooling

## Backend quick start (local)

Prerequisites:

- Python 3.10+ (tested with 3.14 in this environment)

Commands (from repo root):

```bash
cd ai-bos-backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend endpoints implemented in this starter:

- Auth:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `GET /api/v1/auth/me`
- RBAC endpoints (minimal):
  - `GET /api/v1/rbac/permissions`, `GET /api/v1/rbac/roles`, `GET /api/v1/rbac/users`
- Observability:
  - `GET /health`, `GET /health/details`
- Minimal real module endpoints for the frontend shell (so pages work when mocks are disabled):
  - `/api/v1/platform/organizations`, `/api/v1/platform/notifications`
  - `/api/v1/finance/*` (overview/invoices/transactions)
  - `/api/v1/crm/*` (contacts/leads/activities)
  - `/api/v1/sales/orders`, `/api/v1/marketing/campaigns`
  - `/api/v1/bi/reports`
  - `/api/v1/tasks`
  - `/api/v1/projects`, `/api/v1/calendar/events`, `/api/v1/meetings`

## Frontend quick start (local)

Commands (from repo root):

```bash
cd ai-bos-frontend
npm install
npm run dev
```

Frontend env:

- `VITE_API_URL=http://localhost:8000`
- `VITE_USE_MOCKS=false`
- `VITE_AUTO_DEMO_LOGIN=true` (auto-login on `/` for local development)

If you want to see the real login form:

- open `http://localhost:5173/login`
- or set `VITE_AUTO_DEMO_LOGIN=false` and restart the dev server

## Demo credentials

The backend includes two seeded demo users:

- Owner/Admin: `ceo@demo.aibos.io` / `demo1234`
- Staff: `staff@demo.aibos.io` / `demo1234`

Use these to test RBAC (owner sees more modules than staff).

## Environment variables

### Backend (`ai-bos-backend/.env.example`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Neon / Postgres URL (auto SSL + `postgresql+psycopg2` normalize) |
| `JWT_SECRET` / `SECRET_KEY` | Signing secret (required in production) |
| `CORS_ORIGINS` | Comma-separated frontend origins (**never `*` in prod**) |
| `ENVIRONMENT` | `development` / `staging` / `production` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `SEED_DEMO_DATA` | Seed demo org/users (default `false` in production) |
| `OPENAI_API_KEY` | Optional LLM |
| `SMTP_*` | Transactional email (`SMTP_USERNAME` or `SMTP_USER`) |

### Frontend (`ai-bos-frontend/.env.example`)

| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Backend base URL (e.g. `https://api.example.com`) |
| `VITE_USE_MOCKS` | `false` for real API |
| `VITE_AUTO_DEMO_LOGIN` | Must be `false` in production |
| `VITE_CHATBOT_API_TOKEN` | Must match backend `CHATBOT_API_TOKEN` |

## Database (local Postgres)

```bash
docker compose -f docker-compose.dev.yml up -d
cd ai-bos-backend
cp .env.example .env   # DATABASE_URL points at localhost:5433
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Migrations run automatically on API startup (`alembic upgrade head`). Manual:

```bash
cd ai-bos-backend
alembic upgrade head
```

## Docker

Staging-like full stack:

```bash
docker compose -f docker-compose.staging.yml up --build
```

- API: http://localhost:8000  
- Web: http://localhost:8080  

Backend image uses multi-stage build and `python start.py` (honours `PORT`).

## Production deployment

Target stack: **Vercel** (frontend) · **Render** (API) · **Neon** (Postgres) · **GitHub**.

### 1. Neon PostgreSQL

1. Create a Neon project and copy the connection string.
2. Prefer the **pooled** connection string for the web service.
3. Set `DATABASE_URL` on Render. The app:
   - rewrites `postgres://` → `postgresql+psycopg2://`
   - appends `sslmode=require` when `ENVIRONMENT=production`
4. Keep `SEED_DEMO_DATA=false` in production (create real users via signup/invite).

### 2. Render (backend)

Option A — Blueprint:

```bash
# From repo root after pushing to GitHub
# Connect the repo in Render → apply render.yaml
```

Option B — Manual Web Service:

- **Root directory:** `ai-bos-backend`
- **Build:** `pip install -r requirements.txt`
- **Start:** `python start.py`
- **Health check:** `/health`
- **Python:** 3.12 (see `runtime.txt`)

Required env vars: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` (your Vercel URL), `APP_PUBLIC_URL`, `API_PUBLIC_URL`, `ENVIRONMENT=production`, `SEED_DEMO_DATA=false`.

After deploy, set `API_PUBLIC_URL` to the Render URL and `CORS_ORIGINS` to the Vercel URL(s).

### 3. Vercel (frontend)

- **Root directory:** `ai-bos-frontend` (or use root `vercel.json`)
- **Build:** `npm run build`
- **Output:** `dist`
- SPA rewrites are in `vercel.json`

Env:

```
VITE_API_URL=https://<your-render-service>.onrender.com
VITE_USE_MOCKS=false
VITE_AUTO_DEMO_LOGIN=false
VITE_CHATBOT_API_TOKEN=<same as Render CHATBOT_API_TOKEN>
```

Redeploy after changing `VITE_*` (they are compile-time).

### Known production limits

- Refresh sessions are **in-memory** → stay on **1 worker / 1 instance** until Redis/DB sessions exist.
- Document storage defaults to local disk; use S3/MinIO env vars for durable uploads on Render.
- OpenAPI `/docs` is disabled when `ENVIRONMENT=production`.

## Testing

Backend tests:

```bash
cd ai-bos-backend
python -m pytest -q
```

Frontend:

```bash
cd ai-bos-frontend
npm run typecheck
npm run build
```

## Troubleshooting

| Symptom | Check |
|---|---|
| CORS errors in browser | `CORS_ORIGINS` must include exact Vercel origin (`https://…`) |
| 500 on login after scale-out | In-memory refresh store — use 1 instance |
| Neon SSL / connection refused | URL + `sslmode=require`; allow Render egress |
| Frontend calls localhost | `VITE_API_URL` missing at build time |
| Empty DB in prod | Expected with `SEED_DEMO_DATA=false` — invite/register users |
| Migrations fail on boot | Neon cold start — app retries 5×; check `DATABASE_URL` |

## License / ownership

Documentation and code are owned and maintained by the AI BOS Platform Team.
Copyright 2026 AI BOS. All rights reserved.

