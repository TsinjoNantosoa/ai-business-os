# AI BOS Backend — production / staging image (multi-stage)
FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin aibos

COPY --from=builder /install /usr/local
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
COPY start.py .

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    SEED_DEMO_DATA=false \
    STORAGE_LOCAL_PATH=/data/storage \
    BACKUP_DIR=/data/backups \
    PORT=8000

RUN mkdir -p /data/storage /data/backups \
    && chown -R aibos:aibos /app /data

USER aibos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8000}/health || exit 1

CMD ["python", "start.py"]
