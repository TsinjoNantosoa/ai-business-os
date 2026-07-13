# Staging environment — AI BOS (S18)

## Objectif

Stack **pré-prod locale / CI** alignée Postgres + API + frontend, sans dépendance AWS obligatoire.

## Démarrage local

```bash
cd ai-bos
cp .env.staging.example .env.staging
# Éditer JWT_SECRET / mots de passe

docker compose -f docker-compose.staging.yml --env-file .env.staging up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health/details (`environment=staging`) |
| Postgres | localhost:5432 |

Comptes démo inchangés (`ceo@demo.aibos.io` / `demo1234`) après bootstrap.

## Images Docker

- `ai-bos-backend/Dockerfile`
- `ai-bos-frontend/Dockerfile` (+ `nginx.conf`)

## CD GitHub Actions

Workflow [`.github/workflows/cd-staging.yml`](../.github/workflows/cd-staging.yml) :

1. Build & push `ghcr.io/<owner>/aibos-api:staging` et `aibos-web:staging` sur push `main`
2. Valide `docker compose … config`

Déploiement cloud (ECS/K8s) : brancher ensuite les images GHCR sur l’infra staging (hors scope MVP).

## Checklist staging

- [ ] `docker compose … up` healthy
- [ ] Login CEO OK
- [ ] `/health/details` → `"environment": "staging"`
- [ ] Backup : `POST /api/v1/platform/backups`
- [ ] Migration Alembic au boot API
