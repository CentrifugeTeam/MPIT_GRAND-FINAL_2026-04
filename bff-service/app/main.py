from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, notification, report_tasks, websocket
from app.core.config import get_settings
from app.middleware.rate_limit import RedisRateLimitMiddleware
from app.middleware.request_audit import RequestAuditMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.analytics_mq_consumer import start_consumer, stop_consumer
    from app.services.chat_mq import chat_bus

    s = get_settings()
    app.state.redis_client = None
    if (s.REDIS_URL or "").strip():
        app.state.redis_client = redis.from_url(
            s.REDIS_URL.strip(), encoding="utf-8", decode_responses=True
        )

    await chat_bus.start()
    start_consumer()
    yield
    await stop_consumer()
    await chat_bus.stop()
    rc = getattr(app.state, "redis_client", None)
    if rc is not None:
        await rc.aclose()
        app.state.redis_client = None


app = FastAPI(
    title="BFF Service",
    description=(
        "Единая точка входа для фронтенда: аутентификация, аналитика NL→SQL, "
        "уведомления, отчётные задачи. Схемы ответов дублируют upstream для Swagger."
    ),
    version="1.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "auth",
            "description": "Регистрация, вход, refresh, профиль и роли (прокси auth-service).",
        },
        {
            "name": "analytics",
            "description": "Схема БД, interpret, чаты, история, источники данных (прокси analytics-service).",
        },
        {
            "name": "report-tasks",
            "description": "Расписания и прогоны отчётов (прокси report-task-service).",
        },
        {
            "name": "notification",
            "description": "Уведомления и настройки (прокси notification-service).",
        },
        {
            "name": "websocket",
            "description": "Токен и служебные HTTP для WebSocket (детальная OpenAPI для WS не дорабатывалась).",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestAuditMiddleware)
app.add_middleware(RedisRateLimitMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(notification.router, prefix="/api/notification", tags=["notification"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(report_tasks.router, prefix="/api/analytics", tags=["report-tasks"])
app.include_router(websocket.router, prefix="/api/websocket", tags=["websocket"])


@app.get("/")
async def root():
    return {"message": "BFF Service is running"}
