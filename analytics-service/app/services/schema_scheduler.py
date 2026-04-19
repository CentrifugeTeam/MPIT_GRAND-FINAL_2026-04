from apscheduler.schedulers.background import BackgroundScheduler

from app.services.db_schema import introspect_public
from app.services import schema_cache

_scheduler: BackgroundScheduler | None = None


def refresh_schema_cache() -> None:
    """Сброс кэша и повторное чтение information_schema (cron / ручной вызов)."""
    from app.api.analytics import get_engine as ge

    schema_cache.invalidate()
    engine = ge()
    try:
        tables = introspect_public(engine)
        schema_cache.set_cached(tables)
    except Exception:
        pass


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
    _scheduler.start()


def stop_schema_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
