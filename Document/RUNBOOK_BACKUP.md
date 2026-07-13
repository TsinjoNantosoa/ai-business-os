# Backup & restore — AI BOS (S17)

## Objectifs RPO / RTO (MVP)

| Scénario | RPO | RTO |
|----------|-----|-----|
| Corruption / erreur ops | ≤ 24 h (backup quotidien) | ≤ 8 h |
| Perte disque local | dernier zip `BACKUP_DIR` | restore + restart API |

## Contenu d’un backup

Archive ZIP `backup_YYYYMMDD_HHMMSS_xxxxxxxx.zip` :

- `manifest.json` — métadonnées (engine, env, timestamps)
- `database/aibos.db` (SQLite) **ou** `database/aibos.dump` (Postgres `pg_dump -Fc`)
- `storage/**` — fichiers documents locaux (optionnel)

## CLI

```bash
cd ai-bos-backend

# Créer
python -m scripts.backup
python -m scripts.backup --no-storage

# Restaurer (confirmation RESTORE)
python -m scripts.restore backup_20260713_120000_12345678 --yes
```

Variables :

- `BACKUP_DIR` (défaut `./backups`)
- `DATABASE_URL`
- `STORAGE_LOCAL_PATH`

## API (owner / `admin.audit`)

```http
GET  /api/v1/platform/backups
POST /api/v1/platform/backups
POST /api/v1/platform/backups/{id}/restore   # body: {"confirm":"RESTORE"}
```

Restore via API **interdit** si `ENVIRONMENT=production` (utiliser CLI + runbook).

## Postgres

Sur staging/prod Postgres, le service appelle `pg_dump` / `pg_restore` (binaires requis sur l’hôte/image ops).  
L’image API slim n’embarque pas `postgresql-client` ; pour dumps Postgres, exécuter le CLI depuis un job ops ou étendre l’image.

## Cadence recommandée

- Quotidien : `python -m scripts.backup` (cron / Task Scheduler)
- Avant migration Alembic majeure : backup manuel
- Après restore : redémarrer uvicorn + vérifier `/health/details`
