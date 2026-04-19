from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_engine = create_engine(
    _settings.PLATFORM_DATABASE_URL,
    pool_pre_ping=True,
)
PlatformSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def platform_engine():
    return _engine


def _migrate_nl_sql_jobs_user_id_to_uuid() -> None:
    """Старые инсталляции создавали user_id как varchar — без приведения JOIN с users.uuid ломается."""
    with _engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'nl_sql_jobs'
                  AND column_name = 'user_id'
                """
            )
        ).fetchone()
        if not row:
            return
        dt = row[0]
        if dt not in ("character varying", "varchar", "text"):
            return
    with _engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE nl_sql_jobs "
                "ALTER COLUMN user_id TYPE uuid USING trim(user_id)::uuid"
            )
        )


def init_platform_tables():
    from app.db.platform_base import PlatformBase
    from app.db.platform_models import NlSqlJob  # noqa: F401

    PlatformBase.metadata.create_all(bind=_engine)
    _migrate_nl_sql_jobs_user_id_to_uuid()
