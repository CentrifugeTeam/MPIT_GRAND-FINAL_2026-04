"""Разрешение URL аналитической БД по source_key (таблица analytics_data_sources в platform)."""

from sqlalchemy import create_engine, text

from app.core.config import get_settings


def resolve_analytics_database_url(source_key: str | None) -> str:
    settings = get_settings()
    sk = (source_key or "").strip().lower() or None
    env_pref = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip().lower()
    eng = create_engine(settings.PLATFORM_DATABASE_URL, pool_pre_ping=True)
    try:
        with eng.connect() as conn:
            if sk:
                r = conn.execute(
                    text(
                        "SELECT database_url FROM analytics_data_sources "
                        "WHERE source_key = :k LIMIT 1"
                    ),
                    {"k": sk},
                ).fetchone()
                if r:
                    return str(r[0]).strip()
            if env_pref:
                r_env = conn.execute(
                    text(
                        "SELECT database_url FROM analytics_data_sources "
                        "WHERE source_key = :k LIMIT 1"
                    ),
                    {"k": env_pref},
                ).fetchone()
                if r_env:
                    return str(r_env[0]).strip()
            r = conn.execute(
                text(
                    "SELECT database_url FROM analytics_data_sources "
                    "WHERE is_default = true LIMIT 1"
                )
            ).fetchone()
            if r:
                return str(r[0]).strip()
            r2 = conn.execute(
                text(
                    "SELECT database_url FROM analytics_data_sources "
                    "ORDER BY source_key LIMIT 1"
                )
            ).fetchone()
            if r2:
                return str(r2[0]).strip()
    finally:
        eng.dispose()
    return settings.ANALYTICS_DATABASE_URL.strip()
