# Load tests AI BOS (k6) — S20

Baseline performance pour l’API locale / staging.

## Prérequis

1. Backend démarré : `python -m uvicorn app.main:app --port 8000`
2. [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) installé

```bash
# Windows (Chocolatey)
choco install k6

# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D70
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6
```

## Scénarios

| Script | Scénario | Défaut |
|--------|----------|--------|
| `smoke.js` | LT-001 health + login + contacts + KPIs | 10 VUs / 30 s |
| `login_burst.js` | LT-002 burst login | ramp 0→50 |

## Commandes

```bash
cd ai-bos-backend

# Smoke baseline
k6 run tests/perf/smoke.js

# Custom
k6 run -e API_URL=http://127.0.0.1:8000 -e VUS=20 -e DURATION=1m tests/perf/smoke.js

# Login burst
k6 run tests/perf/login_burst.js
```

## Fallback Python (sans k6)

```bash
python tests/perf/smoke_httpx.py
```

## Seuils smoke (local SQLite)

- `http_req_failed` < 1 %
- p95 contacts / KPIs < 800 ms
- p95 login < 4000 ms (bcrypt sous charge)
- p95 global < 3500 ms

Baseline mesurée (2026-07-13) :
- k6 smoke 5 VUs / 15 s : 100 % checks ; contacts p95 ≈ 33 ms · KPIs ≈ 21 ms · login ≈ 2.1 s
- `smoke_httpx.py` 8×5 : health ≈ 36 ms · contacts ≈ 66 ms · KPIs ≈ 37 ms · login ≈ 2.3 s
