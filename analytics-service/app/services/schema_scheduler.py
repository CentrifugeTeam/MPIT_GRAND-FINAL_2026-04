from apscheduler.schedulers.background import BackgroundScheduler

from app.core.queues import QUEUE_REPORT_TASK_INCOMING
from app.services.db_schema import introspect_public
from app.services import schema_cache
from app.services.chat_store import reserve_due_report_sessions
from app.services.rabbitmq_publish import rabbit_publish

import asyncio

_scheduler: BackgroundScheduler | None = None


def refresh_schema_cache() -> None:
    """Сброс кэша и повторное чтение information_schema (cron / ручной вызов)."""
    from app.services.analytics_db import get_analytics_engine
    from app.services.data_sources_store import list_active_source_keys

    schema_cache.invalidate()
    keys = list_active_source_keys()
    if not keys:
        keys = [None]
    for sk in keys:
        raw = sk if sk else None
        try:
            engine = get_analytics_engine(raw)
            tables = introspect_public(engine)
            schema_cache.set_cached(tables, raw)
        except Exception:
            pass


def dispatch_due_report_tasks() -> None:
    due_rows = reserve_due_report_sessions(limit=100)
    if not due_rows:
        return
    for row in due_rows:
        prompt = str(row.get("preview_text") or row.get("title") or "").strip()
        if not prompt:
            prompt = "Сформируй плановый отчет по текущим данным."
        payload = {
            "conversation_id": row["conversation_id"],
            "user_id": row["user_id"],
            "message_id": f"report-{row['conversation_id']}-{row['runs_count']}",
            "content": prompt,
            "scheduled_report": True,
            "notification_email": row.get("notification_email"),
        }
        try:
            asyncio.run(rabbit_publish.publish_json(QUEUE_REPORT_TASK_INCOMING, payload))
        except Exception:
            continue


def start_schema_scheduler(cron_hour: int) -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        refresh_schema_cache,
        "cron",
        hour=cron_hour,
        minute=0,
        id="schema_refresh_24h",
        replace_existing=True,
    )
    _scheduler.add_job(
        dispatch_due_report_tasks,
        "interval",
        minutes=1,
        id="report_tasks_dispatch",
        replace_existing=True,
    )
    _scheduler.start()


def stop_schema_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
