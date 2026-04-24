import logging

from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.api import notifications
from app.database import engine, Base

_log = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


def _migrate_notifications_payload_column() -> None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'notifications'
                  AND column_name = 'payload'
                """
            )
        ).fetchone()
    if row:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE notifications ADD COLUMN payload JSONB"))


_migrate_notifications_payload_column()


def _ensure_notification_type_chat_invite() -> None:
    """Старые БД: нативный PG enum не содержит chat_invite — INSERT падает, BFF молчит."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT c.udt_name
                FROM information_schema.columns c
                WHERE c.table_schema = 'public'
                  AND c.table_name = 'notifications'
                  AND c.column_name = 'type'
                """
            )
        ).fetchone()
    if not row or not row[0]:
        return
    typname = str(row[0])
    with engine.connect() as conn:
        kind = conn.execute(
            text("SELECT typtype FROM pg_type WHERE typname = :tname"),
            {"tname": typname},
        ).fetchone()
    if not kind or str(kind[0]) != "e":
        return
    with engine.begin() as conn:
        ex = conn.execute(
            text(
                """
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = :tname
                  AND e.enumlabel = 'chat_invite'
                """
            ),
            {"tname": typname},
        ).fetchone()
        if ex:
            return
        try:
            conn.execute(text(f'ALTER TYPE "{typname}" ADD VALUE \'chat_invite\''))
        except Exception as e:
            _log.warning("skip enum chat_invite migration: %s", e)


_ensure_notification_type_chat_invite()

app = FastAPI(
    title="Notification Service",
    description="Уведомления и настройки; доставка email через RabbitMQ.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "notifications", "description": "CRUD уведомлений, настройки, постановка в очередь."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
