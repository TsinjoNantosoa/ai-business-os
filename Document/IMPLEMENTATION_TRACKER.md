# AI BOS — Tracker d'implémentation (pas à pas)

> **Objectif :** Implémenter le projet étape par étape **sans re-prompt**.  
> Cocher `[x]` uniquement après **test validé** (backend : `pytest`, frontend : `typecheck` / `build` / tests).  
> **Dernière mise à jour :** 2026-07-21 15:11 (UTC+3)

---

## Comment utiliser ce document

1. Travailler **dans l'ordre** des sections (P0 → P1 → P2 → Phases roadmap).
2. Pour chaque étape : implémenter → tester → cocher `[x]` → ajouter une ligne au journal dans `README_ETAT_IMPLEMENTATION.md`.
3. **Ne pas sauter** les tests : une étape non testée reste `[ ]`.
4. Pattern backend pour un nouveau module :
   - Ajouter les données dans `ai-bos-backend/app/data/seed.py` (ou repository DB plus tard).
   - Créer `routes_<module>.py` avec `require_auth` sur chaque endpoint.
   - Enregistrer le router dans `app/main.py`.
   - Ajouter tests dans `tests/test_<module>.py`.
   - Vérifier que `services.ts` pointe vers le même chemin API.

---

## P0 — Fondation (terminé)

- [x] P0.1 Monorepo scaffold
- [x] P0.2 `core/identity` (JWT login/refresh/me)
- [x] P0.3 `core/authorization` (RBAC)
- [x] P0.4 `core/observability` (logs, metrics, correlation ID)
- [x] P0.5 Frontend branché (`VITE_API_URL`, mocks off)

---

## P1 — Endpoints réels (remplacer mocks frontend)

### P1.A — Auth & Platform

| Étape | Endpoint | Fichier route | Test | Statut |
|-------|----------|---------------|------|--------|
| P1.A.1 | `POST /api/v1/auth/login` | `routes_auth.py` | `test_auth.py` | [x] |
| P1.A.2 | `POST /api/v1/auth/refresh` | `routes_auth.py` | `test_auth.py` | [x] |
| P1.A.3 | `GET /api/v1/auth/me` | `routes_auth.py` | `test_auth.py` | [x] |
| P1.A.4 | `GET /api/v1/rbac/*` | `routes_rbac.py` | `test_rbac.py` | [x] |
| P1.A.5 | `GET /api/v1/platform/organizations` | `routes_platform.py` | smoke | [x] |
| P1.A.6 | `GET /api/v1/platform/notifications` | `routes_platform.py` | `test_remaining_modules.py` | [x] |
| P1.A.7 | `GET /api/v1/platform/audit-logs` | `routes_platform.py` | `test_remaining_modules.py` | [x] |

### P1.B — CRM & Sales

| Étape | Endpoint | Statut |
|-------|----------|--------|
| P1.B.1 | `GET /api/v1/crm/contacts` | [x] |
| P1.B.2 | `GET /api/v1/crm/leads` | [x] |
| P1.B.3 | `GET /api/v1/crm/activities` | [x] |
| P1.B.4 | `GET /api/v1/sales/orders` | [x] |
| P1.B.5 | `GET /api/v1/marketing/campaigns` | [x] |

### P1.C — Finance

| Étape | Endpoint | Statut |
|-------|----------|--------|
| P1.C.1 | `GET /api/v1/finance/overview` | [x] |
| P1.C.2 | `GET /api/v1/finance/invoices` | [x] |
| P1.C.3 | `GET /api/v1/finance/transactions` | [x] |

### P1.D — Projects & Ops

| Étape | Endpoint | Statut |
|-------|----------|--------|
| P1.D.1 | `GET /api/v1/projects` | [x] |
| P1.D.2 | `GET /api/v1/tasks` | [x] |
| P1.D.3 | `GET /api/v1/calendar/events` | [x] |
| P1.D.4 | `GET /api/v1/meetings` | [x] |
| P1.D.5 | `GET /api/v1/support/tickets` | [x] |

### P1.E — HR

| Étape | Endpoint | Statut |
|-------|----------|--------|
| P1.E.1 | `GET /api/v1/hr/employees` | [x] |
| P1.E.2 | `GET /api/v1/hr/jobs` | [x] |
| P1.E.3 | `GET /api/v1/hr/candidates` | [x] |

### P1.F — Business modules

| Étape | Endpoint | Statut |
|-------|----------|--------|
| P1.F.1 | `GET /api/v1/contracts` | [x] |
| P1.F.2 | `GET /api/v1/knowledge/articles` | [x] |
| P1.F.3 | `GET /api/v1/workflows` | [x] |
| P1.F.4 | `GET /api/v1/ai/agents` | [x] |
| P1.F.5 | `GET /api/v1/inventory/items` | [x] |
| P1.F.6 | `GET /api/v1/documents` | [x] |
| P1.F.7 | `GET /api/v1/procurement/suppliers` | [x] |
| P1.F.8 | `GET /api/v1/procurement/purchase-orders` | [x] |

### P1.G — Analytics & BI

| Étape | Endpoint | Statut |
|-------|----------|--------|
| P1.G.1 | `GET /api/v1/analytics/kpis` | [x] |
| P1.G.2 | `GET /api/v1/bi/reports` | [x] |
| P1.G.3 | `GET /api/v1/ml/forecast?horizon=7d\|30d\|90d` | [x] |

### P1.H — Qualité frontend (à faire)

| Étape | Action | Commande de validation | Statut |
|-------|--------|------------------------|--------|
| P1.H.1 | Copier `.env.example` → `.env` | `npm run dev` + login OK | [x] |
| P1.H.2 | Ajouter Vitest + test `client.ts` | `npm run test` | [x] |
| P1.H.3 | Ajouter Playwright smoke (login + dashboard) | `npm run test:e2e` | [x] |
| P1.H.4 | Code splitting routes lourdes | `npm run build` bundle < 500 kB gzip | [x] |

---

## P2 — Backend métier avancé

### P2.A — Persistance (PostgreSQL)

- [x] P2.A.1 Modèles SQLAlchemy + Alembic migrations (`organizations`, `users`)
- [x] P2.A.2 Repositories DB — **CRM + finance + workflows + tasks + tickets + documents** migrés
- [x] P2.A.3 Multi-tenant (`org_id` FK sur `users`, index)
- [x] P2.A.4 Tests d'intégration DB (pytest + SQLite — `tests/test_database.py`)

### P2.B — Billing & subscriptions

- [x] P2.B.1 Modèle `Plan`, `Subscription`, `BillingInvoice`
- [x] P2.B.2 Endpoints `GET/POST /api/v1/billing/*`
- [x] P2.B.3 Webhooks Stripe (sandbox + mock sans clés)
- [x] P2.B.4 Page Settings Billing branchée

### P2.C — Workflows exécutables

- [x] P2.C.1 Modèle workflow (trigger, actions, état)
- [x] P2.C.2 Moteur d'exécution synchrone MVP (`WorkflowEngine`)
- [x] P2.C.3 `POST /api/v1/workflows/{id}/run` + `GET /executions`
- [x] P2.C.4 UI : bouton Exécuter + historique depuis API

### P2.D — Agents IA connectés

- [x] P2.D.1 Service LLM (OpenAI si clé, sinon mock intelligent)
- [x] P2.D.2 `POST /api/v1/ai/chat` (streaming SSE)
- [x] P2.D.3 RAG sur knowledge base + contexte métier DB
- [x] P2.D.3b RAG produit : index `Document/*.md`, retrieval hybride, citations chat
- [x] P2.D.4 Copilot frontend branché au backend SSE

### P2.E — CRUD complet (au-delà du GET)

Pour chaque module métier, ajouter dans l'ordre :

- [x] P2.E.1 Contacts : `POST`, `PATCH`, `DELETE`
- [x] P2.E.2 Invoices : création + envoi (`POST /invoices`, `POST /{id}/send`)
- [x] P2.E.3 Tasks : assignation + changement statut (`PATCH /status`, `PATCH /assign`)
- [x] P2.E.3b Tasks : création (`POST /tasks`) + UI Create
- [x] P2.E.4 Tickets : réponses messages (`POST /messages`, `PATCH /status`)
- [x] P2.E.4b Tickets : création (`POST /tickets`) + UI Create
- [x] P2.E.5 Documents : upload local + MinIO/S3 optionnel (`POST /upload`, `GET /download`)
- [x] P2.E.6 Auth profil : `PATCH /auth/me` + `POST /auth/change-password` + Settings Profil
- [x] P2.E.7 Leads : création + stage (`POST /leads`, `PATCH /{id}/stage`) + Pipeline DnD
- [x] P2.E.8 Settings Org Save (`GET/PATCH /organizations/me`)
- [x] P2.E.9 Team revoke invitation + Copilot sources RAG + Analytics CSV + BI NL IA + Projects `/:id`

---

## Phases roadmap produit UX (audit SaaS 2026-07)

### Phase UX 1 — Permissions CEO / nav

- [x] Catalogue `APP_PERMISSIONS` + rôles owner/admin full access (FE + BE owner sync)
- [x] Toutes les routes app gated `RequirePermission`
- [x] Nav Leaves `/app/hr/leaves`

### Phase UX 2 — Mutations Create/Save CRM & Finance

- [x] Contacts Create/Update/Delete + export CSV
- [x] Pipeline Create lead + DnD → PATCH stage (optimistic)
- [x] Factures Create + Send + Voir + export

### Phase UX 3 — Settings / Copilot / Analytics / BI / Projects

- [x] Settings Org load/save
- [x] Copilot SSE `done.sources` (widget + page)
- [x] Team revoke invitation + GDPR erase UI
- [x] Analytics période 3/6/12m + CSV
- [x] BI NL → stream IA + Play rapport
- [x] Route `projects/:id` depuis liste

### Phase UX 4 — Tasks / Tickets / Profil (2026-07-17)

- [x] `POST /api/v1/tasks` + dialog Create Tasks
- [x] `POST /api/v1/support/tickets` + dialog Create Tickets
- [x] `PATCH /api/v1/auth/me` + `POST /api/v1/auth/change-password` + Settings Profil

---

## Lot A — Auth & email (2026-07-21)

- [x] Table + migrations `password_reset_tokens` (015) puis code à 6 chiffres + compteur `attempts` (016)
- [x] `POST /api/v1/auth/forgot-password` avec réponse anti-énumération (envoie un code 6 chiffres par email)
- [x] `POST /api/v1/auth/verify-reset-code` (validation du code, blocage après 5 échecs)
- [x] `POST /api/v1/auth/reset-password` (email + code + nouveau mot de passe) + révocation des refresh sessions
- [x] Service email `log|smtp` + templates code de réinitialisation et invitation
- [x] Pages `/forgot-password` et `/reset-password` en 2 étapes (code → nouveau mot de passe) + i18n FR/EN/AR
- [x] Tests validés (2026-07-21 15:55) : 127 pytest, 8 Vitest, typecheck, smoke HTTP

---

## Phases roadmap (README_40)

### Phase 0 — CORE extraction SIH IA (S2–S8)

- [x] S1 Scaffold + doc + frontend mock-first
- [ ] S2 Extraire `core/config` partagé
- [ ] S3 Extraire `core/database` (connexion pool)
- [ ] S4 Extraire `core/events` (bus interne)
- [ ] S5 Extraire `core/files` (storage abstraction)
- [ ] S6 Extraire `core/notifications` (email/push)
- [ ] S7 Extraire `core/search` (Elasticsearch/OpenSearch)
- [ ] S8 Tests e2e CORE + documentation API OpenAPI complète

### Phase 1 — Platform MVP multi-tenant (S9–S20)

- [x] S9 Onboarding organisation + invitation utilisateurs
- [x] S10 Isolation tenant (middleware + row-level security)
- [x] S11 Feature flags admin
- [x] S12 Audit log persistant (écriture sur chaque mutation)
- [x] S13 Notifications temps réel (WebSocket/SSE)
- [x] S14 Intégrations OAuth Google/Microsoft : Authorization Code + PKCE, callback backend, code SPA à usage unique, mock local uniquement (renforcé le 2026-07-21 à 16:27 UTC+3 ; credentials fournisseurs à renseigner)
- [x] S15 API keys pour intégrations tierces
- [x] S16 Export données (GDPR)
- [x] S17 Backup / restore procédures
- [x] S18 Staging environment
- [x] S19 CI/CD GitHub Actions complet
- [x] S20 Load test baseline (k6)

### Phase 2 — Agent Engine + Workflows (S21–S36)

- [x] S21–S28 Base P2.C / P2.D (workflows run + chat SSE + RAG Document)
- [ ] S29 Tool registry (CRM, Finance, HR tools pour agents)
- [ ] S30 Agent orchestration multi-step
- [ ] S31 Human-in-the-loop approvals
- [ ] S32 Workflow designer UI (drag & drop)
- [ ] S33 Event-driven triggers (webhooks entrants)
- [ ] S34 Observability agents (traces, coûts tokens)
- [ ] S35 Rate limiting + quotas par plan
- [ ] S36 Documentation agents pour clients

### Phase 3 — Verticales + scale cloud (S37–S52)

- [ ] S37 Module Edu (étudiants, cours, notes)
- [ ] S38 Module Legal (dossiers, échéances)
- [ ] S39 Kubernetes manifests (Helm)
- [ ] S40 Auto-scaling HPA
- [ ] S41 CDN assets frontend
- [ ] S42 Multi-région (EU + US)
- [ ] S43 SOC2 readiness checklist
- [ ] S44–S52 Voir `README_36_FutureApplications.md`

---

## Commandes de validation rapides

```bash
# Backend (depuis ai-bos-backend/)
python -m pytest -q
uvicorn app.main:app --reload --port 8000

# Frontend (depuis ai-bos-frontend/)
cp .env.example .env   # ou copier manuellement sous Windows
npm install
npm run typecheck
npm run build
npm run dev
```

**Comptes démo :** `ceo@demo.aibos.io` / `demo1234` — `staff@demo.aibos.io` / `demo1234`

---

## Prochaine action recommandée (sans re-prompt)

**Phases UX 1–4 livrées** (permissions, CRM/Finance mutations, Settings/Copilot/BI, Tasks/Tickets create, profil/password).  
Voir aussi : [`ETAT_PROJET_COMPLET.md`](./ETAT_PROJET_COMPLET.md) · [`README_ETAT_IMPLEMENTATION.md`](./README_ETAT_IMPLEMENTATION.md).  

**Suite suggérée :**
1. ~~Lot B : Marketing/Sales/Projects `POST` create~~ ✅ terminé le 2026-07-21 (migration 017, POST/PATCH + UI sur les 5 modules)
2. ~~Calendar/Meetings create/update~~ ✅ terminé le 2026-07-21
3. **S29** tool registry agents / finaliser **S6** email staging
