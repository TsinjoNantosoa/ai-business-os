from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from sqlalchemy import text
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import configure_logging, log_event
from app.core.metrics import inc, snapshot
from app.core.migrations import run_migrations
from app.core.tenant import clear_current_org_id
from app.presentation.routes_auth import build_auth_router
from app.presentation.routes_platform import build_platform_router
from app.presentation.routes_rbac import build_rbac_router
from app.presentation.routes_dashboard_data import build_dashboard_data_router
from app.presentation.routes_crm_contacts import build_crm_contacts_router
from app.presentation.routes_crm_leads import build_crm_leads_router
from app.presentation.routes_sales_marketing import build_sales_marketing_router
from app.presentation.routes_finance import build_finance_router
from app.presentation.routes_workflows import build_workflows_router
from app.presentation.routes_ai import build_ai_router
from app.presentation.routes_bi import build_bi_router
from app.presentation.routes_tasks import build_tasks_router
from app.presentation.routes_support import build_support_router
from app.presentation.routes_documents import build_documents_router
from app.presentation.routes_projects_calendar_meetings import build_projects_calendar_meetings_router
from app.presentation.routes_hr_recruitment import build_hr_recruitment_router
from app.presentation.routes_operations import build_operations_router
from app.presentation.routes_analytics_ml import build_analytics_ml_router
from app.presentation.routes_procurement import build_procurement_router
from app.presentation.routes_billing import build_billing_router
from app.presentation.routes_feature_flags import build_feature_flags_router
from app.presentation.routes_notifications import build_notifications_router
from app.presentation.routes_api_keys import build_api_keys_router
from app.presentation.routes_oauth import build_oauth_router
from app.presentation.routes_gdpr import build_gdpr_router
from app.presentation.routes_backup import build_backup_router
from app.presentation.routes_knowledge import build_knowledge_router
from app.presentation.routes_events import build_events_router
from app.services.auth_service import AuthService
from app.services.bootstrap import bootstrap_demo_data
from app.services.email_service import EmailService
from app.services.rag_ingest import ensure_rag_index
from app.services.session_store import DatabaseRefreshSessionStore

configure_logging()

logger = logging.getLogger("aibos")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import threading

    run_migrations()
    configure_logging(force=True)
    logger.info("migrations_ready")
    if settings.seed_demo_data:
        with SessionLocal() as session:
            bootstrap_demo_data(session)
        logger.info("demo_data_ready SEED_DEMO_DATA=true")
    else:
        logger.info("demo_data_skipped set SEED_DEMO_DATA=true to fill demo modules")

    def _index_rag() -> None:
        try:
            with SessionLocal() as session:
                ensure_rag_index(session)
            logger.info("rag_index_ready")
        except Exception:
            logger.exception("rag_index_failed")

    # Defer RAG so API is available immediately (large Document/*.md can block for minutes).
    threading.Thread(target=_index_rag, daemon=True, name="rag-index").start()
    logger.info("database_ready environment=%s", settings.environment)
    yield


_docs_url = None if settings.is_production else "/docs"
_redoc_url = None if settings.is_production else "/redoc"
_openapi_url = None if settings.is_production else "/openapi.json"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
# Origins come from CORS_ORIGINS / APP_PUBLIC_URL — never "*".
# Methods/headers "*" is required so browser preflight (OPTIONS) succeeds.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)

logger.info("cors_origins=%s", settings.cors_origins)

# Refresh sessions are persisted so rotation and revocation survive restarts.
session_store = DatabaseRefreshSessionStore()
email_service = EmailService(
    mode=settings.email_mode,
    smtp_host=settings.smtp_host,
    smtp_port=settings.smtp_port,
    smtp_use_tls=settings.smtp_use_tls,
    smtp_user=settings.smtp_user,
    smtp_password=settings.smtp_password,
    sender=settings.smtp_from,
)
from app.services.event_bus import set_email_service

set_email_service(email_service)
auth_service = AuthService(session_store=session_store, email_service=email_service)
app.include_router(build_auth_router(auth_service))
app.include_router(build_oauth_router(auth_service))
app.include_router(build_rbac_router(auth_service))
app.include_router(build_platform_router(email_service))
app.include_router(build_gdpr_router())
app.include_router(build_backup_router())
app.include_router(build_knowledge_router())
app.include_router(build_dashboard_data_router())
app.include_router(build_crm_contacts_router())
app.include_router(build_crm_leads_router())
app.include_router(build_sales_marketing_router())
app.include_router(build_finance_router())
app.include_router(build_workflows_router())
app.include_router(build_ai_router())
app.include_router(build_bi_router())
app.include_router(build_tasks_router())
app.include_router(build_support_router())
app.include_router(build_documents_router())
app.include_router(build_projects_calendar_meetings_router())
app.include_router(build_hr_recruitment_router())
app.include_router(build_operations_router())
app.include_router(build_analytics_ml_router())
app.include_router(build_procurement_router())
app.include_router(build_billing_router())
app.include_router(build_feature_flags_router())
app.include_router(build_notifications_router())
app.include_router(build_api_keys_router())
app.include_router(build_events_router())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")
    headers = dict(exc.headers or {})
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "detail": exc.detail,
            "correlation_id": correlation_id,
        },
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")
    headers = {"X-Correlation-ID": correlation_id} if correlation_id else {}
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "detail": "Validation error",
            "errors": exc.errors(),
            "correlation_id": correlation_id,
        },
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None) or str(uuid.uuid4())
    logger.exception(
        "unhandled_exception path=%s method=%s correlation_id=%s",
        request.url.path,
        request.method,
        correlation_id,
    )
    inc("http_errors_5xx")
    detail = "Internal server error"
    if not settings.is_production:
        detail = f"{type(exc).__name__}: {exc}"
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "detail": detail,
            "correlation_id": correlation_id,
        },
        headers={"X-Correlation-ID": correlation_id},
    )


@app.middleware("http")
async def request_context_middleware(request, call_next):
    clear_current_org_id()
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except RuntimeError as exc:
            if str(exc) != "No response returned.":
                raise
            # Starlette raises this when the client cancels navigation while a
            # response is in flight. Treat it as a client-closed request, not a
            # server failure that pollutes production error telemetry.
            response = Response(status_code=499)
    finally:
        clear_current_org_id()
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    inc("http_requests")
    if response.status_code >= 500:
        inc("http_errors_5xx")

    log_event(
        logger,
        logging.INFO,
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=elapsed_ms,
        correlation_id=correlation_id,
    )

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/")
def root() -> dict[str, object]:
    return {
        "service": settings.app_name,
        "status": "ok",
        "health": "/health",
        "docs": None if settings.is_production else "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def readiness() -> dict[str, str]:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready",
        ) from exc
    return {"status": "ready", "database": "ok"}


@app.get("/health/details")
def health_details() -> dict[str, object]:
    db_status = "ok"
    try:
        with SessionLocal() as session:
            session.connection()
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "environment": settings.environment,
        "database": db_status,
        "cors_origins": settings.cors_origins,
        "metrics": snapshot(),
    }
