# AI BOS — Étape suivante (déjà fait vs reste)

> **Dernière mise à jour :** 2026-07-21 15:11 (UTC+3)
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
| **Prochaine étape produit** | 🟡 Lot B — CRUD Sales / Marketing / Projects / Calendar |
| **Prochaine étape technique (roadmap)** | 🟡 Phase 2 avancée — **S29 Tool registry** |
| Verticales Edu / Legal + scale cloud (Phase 3) | ❌ Pas démarré |

**Aujourd’hui :** le produit est **démo-ready** en local (login → dashboard → CRM / factures / tâches / copilote / admin).  
**Ensuite :** enrichir les modules encore en lecture seule, brancher l’email, puis industrialiser les agents (tools + designer workflows).

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
- [x] OAuth Google / Microsoft (mock + live ready)
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
| Workflows | 🟡 MVP | Persistance + `POST /run` + historique (pas de designer visuel) |
| Agents / Copilot | 🟡 Base | Chat SSE + RAG `Document/*.md` + citations |
| Organizations / Team / Invitations | ✅ | Onboarding + revoke |
| Analytics / BI / ML | 🟡 | Lecture + CSV + BI NL ; forecast seed |
| Sales / Marketing / Projects / HR / Inventory / Procurement / Accounting / Payroll | 🟡 | UI + GET seed — **peu ou pas de POST** |

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
| **S29** | Tool registry (outils CRM / Finance / HR appelables par agents) | [ ] **← commencer ici côté IA** |
| **S30** | Orchestration multi-step (chaînes d’agents) | [ ] |
| **S31** | Human-in-the-loop (approbation avant action sensible) | [ ] |
| **S32** | Workflow designer UI (drag & drop, style React Flow) | [ ] |
| **S33** | Triggers event-driven (webhooks entrants) | [ ] |
| **S34** | Observabilité agents (traces, coûts tokens) | [ ] |
| **S35** | Rate limiting + quotas par plan (hard limits) | [ ] |
| **S36** | Documentation agents pour clients | [ ] |

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
| HR payroll, accounting détaillé, inventory write | UI + GET seed | CRUD DB |
| Stripe | Mock / sandbox | Clés live + customer portal |
| Redis | In-memory process | Pub/sub multi-instance |
| ABAC | Documenté seulement | Implémentation réelle |
| Event Bus | Absent | Redis Streams / outbox |
| pgvector | Embeddings locaux | Vector DB production |

---

## 4. Plan d’exécution — **prochaine itération**

Cocher au fur et à mesure. Mettre à jour la date/heure en tête de fichier à chaque lot terminé.

### Lot A — Auth & email — ✅ terminé le 2026-07-21 à 15:11 (UTC+3)

- [x] A1. `POST /auth/forgot-password` + `POST /auth/reset-password`
- [x] A2. Page frontend `/forgot-password` + `/reset-password`
- [x] A3. Service email (`log` / SMTP) + templates invitation / reset
- [x] A4. Tests : 125 pytest, 9 Vitest, typecheck/build et smoke HTTP validés

### Lot B — Mutations modules seed-only

- [ ] B1. Sales : modèle/repo si besoin + `POST/PATCH` + UI Create
- [ ] B2. Marketing : idem campagnes
- [ ] B3. Projects : `POST/PATCH` + UI
- [ ] B4. Calendar events + Meetings : create/update
- [ ] B5. Tests + journal dans `README_ETAT_IMPLEMENTATION.md`

### Lot C — Agents S29 (dès Lot A/B stables ou en parallèle IA)

- [ ] C1. Schéma Tool registry (nom, permissions, input/output JSON)
- [ ] C2. 3–5 tools MVP : `crm.search_contacts`, `crm.create_lead`, `finance.list_invoices`, `tasks.create`
- [ ] C3. Brancher tool-calling dans `POST /ai/chat` (LLM + garde RBAC)
- [ ] C4. UI Copilot : afficher tool calls / résultats
- [ ] C5. Tests agents + garde-fous (refus si permission manquante)

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
        → [🟡 Phase 2 base IA] ──► VOUS ÊTES ICI
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Lot A Auth/Email   Lot B CRUD     Lot C S29 Tools
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                         S30–S36 Agents & Workflows
                                    ▼
                         Phase 3 Edu / Legal / Scale
```

---

*Document de pilotage pour l’étape suivante. Pour le détail exhaustif, voir `ETAT_PROJET_COMPLET.md`.*
