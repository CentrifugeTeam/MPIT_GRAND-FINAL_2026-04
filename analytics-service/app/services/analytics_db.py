from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_engine_by_url: dict[str, Engine] = {}


def get_analytics_engine(source_key: str | None = None) -> Engine:
    from app.services.data_sources_store import resolve_database_url

    url = resolve_database_url(source_key)
    if url not in _engine_by_url:
        _engine_by_url[url] = create_engine(url, pool_pre_ping=True)
    return _engine_by_url[url]


def dispose_analytics_engine_cache() -> None:
    global _engine_by_url
    for eng in _engine_by_url.values():
        try:
            eng.dispose()
        except Exception:
            pass
    _engine_by_url = {}
