from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.request_audit import RequestAuditMiddleware
from app.api.access_policies import router as access_policies_router
from app.api.analytics import router as analytics_router
from app.api.data_sources import router as data_sources_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.platform_session import init_platform_tables
    from app.services.schema_scheduler import (
        refresh_schema_cache,
        start_schema_scheduler,
        stop_schema_scheduler,
    )
    from app.core.config import get_settings

    init_platform_tables()
    refresh_schema_cache()
    s = get_settings()
    start_schema_scheduler(s.SCHEMA_CRON_HOUR)
    yield
    stop_schema_scheduler()


app = FastAPI(
    title="Analytics NL→SQL Service",
    description="Схема БД, NL-чаты, история; генерация SQL выполняется sql-generator-worker по RabbitMQ.",
    version="1.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestAuditMiddleware)

app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
app.include_router(data_sources_router, prefix="/api/analytics", tags=["analytics-data-sources"])
app.include_router(access_policies_router, prefix="/api/analytics", tags=["analytics-access-policies"])


@app.get("/health")
async def health():
    """Для Docker healthcheck — без зависимостей от RabbitMQ в теле запроса."""
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Analytics service is running"}
