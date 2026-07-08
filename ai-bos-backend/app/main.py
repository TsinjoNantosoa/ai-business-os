from __future__ import annotations

import logging
import time
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging, log_event
from app.core.metrics import inc, snapshot
from app.presentation.routes_auth import build_auth_router
from app.presentation.routes_platform import build_platform_router
from app.presentation.routes_rbac import build_rbac_router
from app.presentation.routes_dashboard_data import build_dashboard_data_router
from app.presentation.routes_crm_contacts import build_crm_contacts_router
from app.presentation.routes_sales_marketing import build_sales_marketing_router
from app.presentation.routes_finance import build_finance_router
from app.presentation.routes_bi import build_bi_router
from app.presentation.routes_tasks import build_tasks_router
from app.presentation.routes_projects_calendar_meetings import build_projects_calendar_meetings_router
from app.services.auth_service import AuthService
from app.services.session_store import InMemoryRefreshSessionStore

configure_logging()

logger = logging.getLogger("aibos")

app = FastAPI(title=settings.app_name, version="0.1.0")

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
app.include_router(build_rbac_router(auth_service))
app.include_router(build_platform_router())
app.include_router(build_dashboard_data_router())
app.include_router(build_crm_contacts_router())
app.include_router(build_sales_marketing_router())
app.include_router(build_finance_router())
app.include_router(build_bi_router())
app.include_router(build_tasks_router())
app.include_router(build_projects_calendar_meetings_router())

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
    return {"status": "ok", "metrics": snapshot()}
