from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import configure_logging, log_event
from app.core.metrics import inc, snapshot
from app.core.migrations import run_migrations
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
from app.services.auth_service import AuthService
from app.services.bootstrap import bootstrap_demo_data
from app.services.session_store import InMemoryRefreshSessionStore

configure_logging()

logger = logging.getLogger("aibos")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations()
    with SessionLocal() as session:
        bootstrap_demo_data(session)
    logger.info("database_ready")
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store = InMemoryRefreshSessionStore()
auth_service = AuthService(session_store=session_store)
app.include_router(build_auth_router(auth_service))
app.include_router(build_oauth_router(auth_service))
app.include_router(build_rbac_router(auth_service))
app.include_router(build_platform_router())
app.include_router(build_gdpr_router())
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

@app.middleware("http")
async def request_context_middleware(request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    started = time.perf_counter()
    response = await call_next(request)
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
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
        "database": db_status,
        "metrics": snapshot(),
    }
