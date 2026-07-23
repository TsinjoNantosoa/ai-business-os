# AI BOS — Étape suivante (déjà fait vs reste)

> **Dernière mise à jour :** 2026-07-23 17:10 (UTC+3)
> **Projet :** AI Business Operating System (`ai-bos`)  
> **But :** Vue claire de ce qui est **déjà implémenté** et de ce qu’il reste à faire pour la **prochaine étape**.  
> **Documents liés :** [`ETAT_PROJET_COMPLET.md`](./ETAT_PROJET_COMPLET.md) · [`IMPLEMENTATION_TRACKER.md`](./IMPLEMENTATION_TRACKER.md) · [`README_40_ImplementationRoadmap.md`](./README_40_ImplementationRoadmap.md) · [`README_ETAT_IMPLEMENTATION.md`](./README_ETAT_IMPLEMENTATION.md)

---

## 1. Verdict en 30 secondes

| Zone | Statut |
|------|--------|
| Documentation entreprise (README_00 → 40) | ✅ Fait |
| Frontend shell + toutes les pages modules | ✅ Fait |
| Backend MVP (auth, RBAC, multi-tenant, modules métier) | ✅ Fait |
| Platform Phase 1 (S9–S20) | ✅ Fait |
| Base IA (chat SSE, RAG, workflows run) | ✅ Fait |
| **Lot A — Auth & email** | ✅ Terminé (SMTP configurable ; credentials staging à fournir) |
| **Lot B — CRUD Sales / Marketing / Projects / Calendar** | ✅ Terminé (DB multi-tenant + POST/PATCH + UI Create) |
| **Lot C — Outils IA pour le Copilot (S29 Tool registry)** | ✅ Terminé (5 tools + SSE tool_call/result + UI chips) |
| **Lot D — S30 orchestration + S31 HITL** | ✅ Terminé (multi-step + pause approbation + ApprovalCard) |
| **Lot E — S32 Workflow designer** | ✅ Terminé (React Flow + definition JSON + CRUD) |
| **Lot F — S33 Triggers event-driven** | ✅ Terminé (domain events + webhooks entrants + dispatch) |
| **Lot G — Exécuteurs workflow** | ✅ Terminé (email / tâche / notify / CRM / agent / API) |
| **Lot H — S34 Observabilité agents** | ✅ Terminé (traces + tokens/coûts + UI Agents) |
| **Lot I — S35 Quotas / rate limits** | ✅ Terminé (RPM plan + tokens mensuels + sièges) |
| **Lot J — S36 Docs agents clients** | ✅ Terminé (guide + API `/ai/docs` + UI) |
| **Persistance 100 % Postgres** | ✅ Terminé (catalog HR/procurement/analytics/agents + `docker-compose.dev.yml`) |
| **Lot K — CRUD catalogue métier** | ✅ Terminé (HR, recruitment, inventory, procurement, accounting + payroll/leaves via employee) |
| **Prochaine étape produit** | 🟡 Phase 3 — Edu AI / Legal / scale (S37+) |
| Verticales Edu / Legal + scale cloud (Phase 3) | ❌ Pas démarré |

**Aujourd’hui :** Phase 2 agents **complète** + dette CRUD catalogue **livrée**.  
**Ensuite :** verticales Edu/Legal (S37+) ou scale cloud.
### Démarrage Postgres local

```bash
docker compose -f docker-compose.dev.yml up -d   # Postgres :5433
# ai-bos-backend/.env → DATABASE_URL=postgresql+psycopg2://aibos:aibos_dev@localhost:5433/aibos
cd ai-bos-backend && alembic upgrade head && uvicorn app.main:app --reload --port 8000
cd ai-bos-frontend && npm run dev
```

---

## 2. Déjà implémenté (livré)

### 2.1 Fondation & plateforme

- [x] Monorepo (`ai-bos-backend`, `ai-bos-frontend`, scaffold `apps/`, `platform/`, …)
- [x] Auth JWT : login / refresh / me / forgot-password / reset-password / change-password / PATCH profil
- [x] RBAC (permissions, rôles, guards FE + BE)
- [x] Multi-tenant (`org_id`, `X-Tenant-Id`, RLS Postgres)
- [x] Observabilité : logs JSON, metrics, `/health`, correlation ID
- [x] Persistance SQLAlchemy + Alembic + seed démo
- [x] Billing (plans, abo, checkout, webhook Stripe mock)
- [x] Feature flags admin + enforcement
- [x] Audit logs persistants
- [x] Notifications in-app SSE
- [x] Email transactionnel `log|smtp` + templates reset / invitation
- [x] API keys M2M
- [x] OAuth Google / Microsoft : Google **live testé** (PKCE + code SPA à usage unique) ; Microsoft prêt (credentials à fournir)
- [x] GDPR export / erase
- [x] Backup / restore + staging Docker + CI/CD GitHub Actions
- [x] Load tests k6 baseline

### 2.2 Modules métier branchés (API réelle + UI)

| Domaine | Niveau | Détail |
|---------|--------|--------|
| CRM contacts / leads / pipeline | ✅ CRUD | Create, update, delete, DnD stage |
| Finance invoices | ✅ CRUD | Create + send |
| Tasks | ✅ CRUD | Create + kanban status/assign |
| Support tickets | ✅ CRUD | Create + messages + status |
| Documents | ✅ | Upload / download (local ou S3) |
| Workflows | 🟡 MVP + designer | Persistance + canvas React Flow + `POST /run` + historique |
| Agents / Copilot | 🟡 Base | Chat SSE + RAG `Document/*.md` + citations |
| Organizations / Team / Invitations | ✅ | Onboarding + revoke |
| Analytics / BI / ML | 🟡 | Lecture + CSV + BI NL ; forecast seed |
| Sales / Marketing / Projects / HR / Inventory / Procurement / Accounting / Payroll | ✅ | CRUD DB (POST/PATCH) + UI Create ; payroll/leaves via employee |

### 2.3 Frontend

- [x] Shell (`AppLayout`, Sidebar, Topbar), i18n FR/EN/AR + RTL
- [x] Auth pages (login, forgot-password, reset-password, 403, onboarding)
- [x] Toutes les routes modules déclarées
- [x] Copilot widget + page
- [x] Qualité : Vitest, Playwright smoke, code splitting
- [x] Branché backend (`VITE_USE_MOCKS=false`)

### 2.4 Comptes démo

| Email | Mot de passe | Rôle |
|-------|--------------|------|
| `ceo@demo.aibos.io` | `demo1234` | owner (org-1) |
| `staff@demo.aibos.io` | `demo1234` | staff (org-1) |
| `ceo@eu.aibos.io` | `demo1234` | owner (org-2, isolation tenant) |

---

## 3. Reste à implémenter (le futur)

### 3.1 Étape suivante immédiate — **Sprint produit (priorité P0)**

Objectif : passer d’une démo « lecture + quelques CRUD » à un SaaS où les modules principaux sont **écrivables** et l’auth complète.

| # | Tâche | Pourquoi | Critère de done |
|---|-------|----------|-----------------|
| **N1** | Forgot password (reset email) | ✅ Terminé | Endpoints + pages FE + token one-shot en DB |
| **N2** | Email SMTP configurable — **S6 partiel** | ✅ Code terminé / 🟡 staging | Mode log local + SMTP ; credentials et réception staging à valider |
| **N3** | Sales orders `POST` + UI Create | Module sales utilisable | Créer une commande depuis le front |
| **N4** | Marketing campaigns `POST` + UI Create | Idem marketing | Créer une campagne |
| **N5** | Projects `POST` / `PATCH` + UI | Projets éditables | Créer / éditer un projet |
| **N6** | Calendar / Meetings mutations | Ops quotidiennes | Créer événement / réunion |

**Ordre recommandé :** N1 → N2 → N3 → N4 → N5 → N6.

### 3.2 Étape suivante technique — **Phase 2 avancée (S29–S36)**

Base déjà livrée : chat SSE, RAG, `workflows/{id}/run`.  
À construire pour l’« Intelligent OS » :

| ID | Tâche | Statut |
|----|-------|--------|
| **S29** | Tool registry (outils CRM / Finance / HR appelables par agents) | [x] ✅ Lot C |
| **S30** | Orchestration multi-step (chaînes d’agents) | [x] ✅ Lot D |
| **S31** | Human-in-the-loop (approbation avant action sensible) | [x] ✅ Lot D |
| **S32** | Workflow designer UI (drag & drop, style React Flow) | [x] ✅ Lot E |
| **S33** | Triggers event-driven (webhooks entrants) | [x] ✅ Lot F |
| **S34** | Observabilité agents (traces, coûts tokens) | [x] ✅ Lot H |
| **S35** | Rate limiting + quotas par plan (hard limits) | [x] ✅ Lot I |
| **S36** | Documentation agents pour clients | [x] ✅ Lot J |

### 3.3 Extraction CORE packages (Phase 0 S2–S8) — dette structurelle

Fonctionne déjà **dans** `ai-bos-backend`, mais pas encore en packages `platform/core-*` séparés :

| ID | Tâche | Priorité |
|----|-------|----------|
| S2 | `core/config` partagé | Moyenne |
| S3 | `core/database` (pool) | Moyenne |
| S4 | `core/events` (bus interne) | Haute (prérequis S33) |
| S5 | `core/files` | Moyenne (déjà abstrait local/S3) |
| S6 | `core/notifications` email/push | Haute (lié à N1/N2) |
| S7 | `core/search` (OpenSearch) | Basse |
| S8 | E2E CORE + OpenAPI versionnée | Haute |

### 3.4 Phase 3 — Verticales & scale (S37–S52) — plus tard

| ID | Tâche |
|----|-------|
| S37–S44 | App **Edu AI** (étudiants, cours, notes, beta) |
| S45–S48 | Scale (PgBouncer, Redis cluster, auto-scaling, CDN) |
| S49–S50 | Marketplace / Plugin SDK |
| S51 | Scaffold **Legal AI** |
| S52 | Buffer + roadmap année 2 |

### 3.5 Dettes produit (hors numérotation S)

| Sujet | Aujourd’hui | Cible |
|-------|-------------|-------|
| HR payroll, accounting détaillé, inventory write | ✅ CRUD DB (Lot K) | — |
| Stripe | Mock / sandbox | Clés live + customer portal |
| Redis | In-memory process | Pub/sub multi-instance |
| ABAC | Documenté seulement | Implémentation réelle |
| Event Bus | Absent | Redis Streams / outbox |
| pgvector | Embeddings locaux | Vector DB production |

---

## 4. Plan d’exécution — **prochaine itération**

Cocher au fur et à mesure. Mettre à jour la date/heure en tête de fichier à chaque lot terminé.

### Lot A — Auth & email — ✅ terminé le 2026-07-21 à 17:10 (UTC+3)

- [x] A1. `POST /auth/forgot-password` + `POST /auth/verify-reset-code` + `POST /auth/reset-password` (code 6 chiffres, anti brute-force)
- [x] A2. Pages frontend `/forgot-password` + `/reset-password` en 2 étapes (code → nouveau mot de passe)
- [x] A3. Service email (`log` / SMTP) + templates invitation / reset ; **SMTP Gmail réel validé**
- [x] A4. OAuth Google **live** (PKCE + code SPA à usage unique) testé bout en bout ; Microsoft prêt (credentials à fournir)
- [x] A5. Tests : 127 pytest, 8 Vitest, typecheck et smoke HTTP validés

### Lot B — Mutations modules seed-only — ✅ terminé le 2026-07-21 à 17:50 (UTC+3)

- [x] B1. Sales : table `sales_orders` (migration 017) + `POST/PATCH /sales/orders` + wizard Create branché (lignes dynamiques, total calculé)
- [x] B2. Marketing : table `campaigns` + `POST/PATCH /marketing/campaigns` + formulaire Create (type, budget, dates)
- [x] B3. Projects : table `projects` + `POST/PATCH /projects` + dialog Create (couleur, budget, échéance)
- [x] B4. Calendar events + Meetings : tables `calendar_events` / `meetings` + create/update + dialogs Create
- [x] B5. Tests : 7 nouveaux pytest (create, patch, 403 permission, isolation tenant org-1/org-2), 136 pytest au total + 11 Vitest + typecheck ; journal mis à jour

> Les 5 modules sont passés du seed en mémoire à de vraies tables multi-tenant (org_id), avec permissions `*.write`, audit log et données démo migrées en DB au bootstrap.

### Lot C — Agents S29 — ✅ terminé le 2026-07-22 à 08:50 (UTC+3)

- [x] C1. Schéma Tool registry (`app/services/tool_registry.py` : nom, permissions, input JSON, handler)
- [x] C2. 5 tools MVP : `crm_search_contacts`, `crm_create_lead`, `finance_list_invoices`, `tasks_create`, `projects_list`
- [x] C3. Tool-calling dans `POST /ai/chat` (OpenAI tools si clé ; mock heuristique sinon) + garde RBAC + audit sur outils mutants
- [x] C4. UI Copilot / Widget : chips `outil · name` / `✓` / `✗` sur les events SSE `tool_call` / `tool_result`
- [x] C5. Tests : `tests/test_ai_tools.py` (registry, 403 permission, SSE tool events) + `GET /api/v1/ai/tools`

> Les agents affichent désormais `toolsCount` réel (= 5). HITL / orchestration multi-step = S30–S31 (Lot D).

### Lot D — S30 orchestration + S31 HITL — ✅ terminé le 2026-07-22 à 10:05 (UTC+3)

- [x] D1. `requires_approval` sur tools mutants + table `ai_pending_actions` (migration 018)
- [x] D2. Orchestrateur multi-step (`agent_orchestrator.py` : rounds outils + pause HITL)
- [x] D3. SSE `step` / `approval_required` + `GET/POST /ai/approvals*` (approve/reject)
- [x] D4. UI `ApprovalCard` (Copilot page + widget) + refresh JWT Copilot
- [x] D5. Tests `test_ai_orchestration.py` (multi-intent, HITL approve/reject)

> Les créations lead/tâche via Copilot demandent une validation humaine avant exécution.

### Lot E — S32 Workflow designer — ✅ terminé le 2026-07-22 à 15:10 (UTC+3)

- [x] E1. Colonne `definition` (migration 019) + dérivation trigger/actions
- [x] E2. API `POST/GET/PATCH /workflows` + canvas React Flow (`@xyflow/react`)
- [x] E3. UI Constructeur : créer / éditer / enregistrer / activer / exécuter
- [x] E4. Tests `test_workflow_designer.py` (7 pytest workflows)

> Le moteur d’exécution reste un stub sync (pas encore d’exécuteurs email/CRM réels). Triggers webhooks = S33.

### Lot F — S33 Triggers event-driven — ✅ terminé le 2026-07-23 à 15:40 (UTC+3)

- [x] F1. Tables `domain_events` + `webhook_endpoints` (migration 021) + `event_id` / `trigger_source` sur exécutions
- [x] F2. `EventBus.publish` + matching workflows actifs via catalogue labels ↔ event types
- [x] F3. API `GET /events`, `/events/catalog`, CRUD webhooks, `POST /webhooks/inbound/{token}` (HMAC optionnel)
- [x] F4. Émission sur create lead / contact / invoice / order
- [x] F5. UI Workflows : onglets Événements + Webhooks ; tests `test_events_s33.py`

### Lot G — Exécuteurs workflow — ✅ terminé le 2026-07-23 à 15:40 (UTC+3)

- [x] G1. `workflow_actions.py` : Envoyer email, Créer tâche, Notifier Slack, Mettre à jour CRM, Run AI agent, Call API
- [x] G2. `WorkflowEngine` exécute les actions réelles + contexte événement
- [x] G3. Tests `test_workflow_actions_lot_g.py` (email outbox, tâche créée, lead → qualified)

### Lot H — S34 Observabilité agents — ✅ terminé le 2026-07-23 à 16:00 (UTC+3)

- [x] H1. Tables `ai_traces` + `ai_llm_calls` (migration 022) + pricing tokens USD
- [x] H2. Instrumentation `LLMService` + `run_chat_orchestration` (SSE `traceId` / tokens / cost)
- [x] H3. API `GET /ai/traces`, `/ai/traces/{id}`, `/ai/usage/summary`
- [x] H4. UI Agents : KPIs usage 30j + table traces ; tests `test_ai_observability_s34.py`

### Lot I — S35 Quotas & rate limits — ✅ terminé le 2026-07-23 à 16:10 (UTC+3)

- [x] I1. Colonne `ai_rpm` sur `billing_plans` (migration 023) — starter 10 / pro 60 / enterprise 200
- [x] I2. `quota_service` : RPM plan + quota tokens mensuels (traces période) + sièges invitations
- [x] I3. Enforcement `POST /ai/chat` → 429 ; `GET /billing/quotas` + overview enrichi
- [x] I4. UI Facturation : RPM + tokens live ; tests `test_quotas_s35.py`

### Lot J — S36 Docs agents clients — ✅ terminé le 2026-07-23 à 16:20 (UTC+3)

- [x] J1. `Document/GUIDE_AGENTS_CLIENT.md` (guide FR Copilot / HITL / outils / quotas / workflows)
- [x] J2. API `GET /ai/docs`, `/ai/docs/guide` + `GET /workflows/templates`
- [x] J3. UI Agents onglet Documentation (outils, templates, guide)
- [x] J4. Tests `test_agent_docs_s36.py`

---

## 5. Comment valider avant de passer au lot suivant

```bash
# Backend
cd ai-bos-backend
python -m pytest -q
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd ai-bos-frontend
npm run typecheck
npm run dev
```

Checklist manuelle :

- [ ] Login `ceo@demo.aibos.io` / `demo1234`
- [ ] Créer une ressource du lot en cours (ex. commande / campagne / projet)
- [ ] Vérifier isolation tenant avec `ceo@eu.aibos.io`
- [ ] Copilot répond (SSE) ; si Lot C : tool call visible

---

## 6. Règle de mise à jour de ce fichier

1. À chaque lot fini : cocher les cases `[x]`.
2. Mettre à jour **date + heure** en tête (`YYYY-MM-DD HH:MM (UTC+3)`).
3. Ajouter une ligne au journal de [`README_ETAT_IMPLEMENTATION.md`](./README_ETAT_IMPLEMENTATION.md).
4. Aligner [`IMPLEMENTATION_TRACKER.md`](./IMPLEMENTATION_TRACKER.md) si un ID Sxx change de statut.

---

## 7. Carte visuelle

```text
[✅ Doc] → [✅ P0 Auth/RBAC] → [✅ P1 GET APIs] → [✅ P2 DB/CRUD clés]
        → [✅ Phase 1 S9–S20 Platform MVP]
        → [✅ Phase 2 Agents S29–S36]
        → [✅ Lot K CRUD catalogue]
                                    ▼
                         Phase 3 Edu / Legal / Scale  ← VOUS ÊTES ICI
```

---

*Document de pilotage pour l’étape suivante. Pour le détail exhaustif, voir `ETAT_PROJET_COMPLET.md`.*
