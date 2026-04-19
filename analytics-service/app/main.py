from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.platform_session import init_platform_tables
    from app.services.rabbitmq_publish import rabbit_publish
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
    await rabbit_publish.connect()
    yield
    await rabbit_publish.close()
    stop_schema_scheduler()


app = FastAPI(
    title="Analytics NL→SQL Service",
    description="Схема БД → очередь → ML SQL generator → результат в БД и RabbitMQ",
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

app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])


@app.get("/health")
async def health():
    """Для Docker healthcheck — без зависимостей от RabbitMQ в теле запроса."""
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Analytics service is running"}
