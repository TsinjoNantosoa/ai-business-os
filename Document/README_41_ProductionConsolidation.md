# AI BOS V2 — Production consolidation

This document describes the implemented runtime, not a future target.

## Tenant boundary

- Every business row carries `org_id`; repositories still filter explicitly as defense in depth.
- PostgreSQL migrations enable and force RLS on tenant tables. The API sets transaction-local `app.current_org_id` from authenticated JWT/API-key claims.
- `X-Tenant-Id` is only a consistency assertion and can never select a different tenant.
- Pre-authentication policies are credential-specific (email, OAuth subject, API-key hash, refresh session id). They permit exact lookups, not table scans.
- `organizations`, `billing_plans`, `feature_flags`, password-reset tokens, and Stripe delivery receipts are control-plane/global tables. Access to them is constrained by their API flows rather than tenant RLS.
- `platform` knowledge documents are globally readable reference material; tenant documents remain isolated.

Run the real PostgreSQL isolation probe with `RLS_DATABASE_URL`:

```bash
alembic upgrade head
RLS_DATABASE_URL=postgresql+psycopg2://... pytest -q tests/test_postgres_rls.py
```

## Authentication and external trust boundaries

- Refresh sessions are database-backed. Only SHA-256 token hashes are stored; rotation, family reuse detection, single logout, logout-all, expiry, device metadata fields, and restart survival are supported.
- The browser receives a Secure/SameSite `HttpOnly` refresh cookie. Zustand does not persist access or refresh tokens in local storage.
- Unknown OAuth identities require a valid pending invitation. They are never attached to a default organization.
- Stripe webhooks require official signature verification. Unsigned events are accepted only when the explicit local-only `ALLOW_UNSIGNED_STRIPE_WEBHOOKS=true` flag is set. Event IDs are persisted for idempotency.
- API keys are stored hashed, shown once, tenant-bound, revocable, and limited to an explicit non-administrative scope allowlist.

## Workflow engine

Executors:

| Executor | Status | Notes |
|---|---|---|
| Email | REAL | Uses configured EmailService; failure is recorded. |
| Create task | REAL | Writes through the tenant repository. |
| CRM update | REAL | Tenant-scoped lead transition. |
| In-app notification / Slack label | PARTIAL | In-app delivery is real; external Slack transport is not configured. |
| HTTP / Call API | REAL | GET/POST/PUT/PATCH/DELETE, timeout, JSON/query/headers, selective retry, redirect denial, DNS/IP SSRF checks. |
| Run AI agent | PARTIAL | Uses the central tool registry with explicit allowlist/max steps; live provider planning remains chat-oriented. |
| Finance/PO legacy labels | PARTIAL | Safe in-app notifications preserve compatibility; they do not create financial records. |

Every run persists step input/output (sanitized), attempts, duration, error, and an idempotency key. Re-delivery of the same domain event reuses the existing workflow execution.

## AI and approvals

The central tool registry declares permission, risk level, read-only status, approval requirement, and tenant scope. LOW reads execute when authorized; MEDIUM mutations pause for requester confirmation; HIGH/CRITICAL self-approval is forbidden. Three deterministic flagship tools provide an executive brief, cashflow drivers, and explainable sales-deal risk scores.

## RAG

Ingestion performs markdown parsing, overlapping chunking, checksums, tenant metadata, embedding, and hybrid lexical/cosine retrieval. `EMBEDDING_PROVIDER=local_hash` is deterministic/offline; `openai` uses the configured embeddings endpoint and records provider/model provenance. Citations are constructed only from retrieved database rows. Retrieved text is marked untrusted in the system prompt and cannot grant tool permissions.

The current vector representation remains JSON and cosine ranking runs in the application. An indexed pgvector or Qdrant backend is the next scaling step; this is intentionally documented as a remaining limitation rather than presented as implemented.

## Operational endpoints

- `/health`: process liveness
- `/ready`: database readiness
- `/health/details`: diagnostic snapshot and counters

Structured logs redact credentials and token-shaped values. AI traces retain provider/model, latency, token usage, cost estimate, tools, status, correlation id, and tenant id.
