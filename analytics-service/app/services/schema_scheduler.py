from apscheduler.schedulers.background import BackgroundScheduler

from app.services.db_schema import introspect_public
from app.services import schema_cache

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
