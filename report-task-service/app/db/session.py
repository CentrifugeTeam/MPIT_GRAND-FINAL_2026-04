from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_engine = create_engine(_settings.PLATFORM_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def platform_engine():
    return _engine


def init_tables() -> None:
    from app.db.base import PlatformBase
    from app.db.models import ReportRun, ReportTask  # noqa: F401

    PlatformBase.metadata.create_all(bind=_engine)
    _migrate_report_runs_schema()


def _migrate_report_runs_schema() -> None:
    with _engine.connect() as conn:
        user_col = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='report_runs'
                  AND column_name='user_id'
                """
            )
        ).fetchone()
        task_col = conn.execute(
            text(
                """
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='report_runs'
                  AND column_name='task_id'
                """
            )
        ).fetchone()
    with _engine.begin() as conn:
        if not user_col:
            conn.execute(text("ALTER TABLE report_runs ADD COLUMN user_id uuid"))
            conn.execute(
                text(
                    """
                    UPDATE report_runs rr
                    SET user_id = rt.user_id
                    FROM report_tasks rt
                    WHERE rr.task_id = rt.id
                    """
                )
            )
            conn.execute(text("ALTER TABLE report_runs ALTER COLUMN user_id SET NOT NULL"))
        if task_col and task_col[0] == "NO":
            conn.execute(text("ALTER TABLE report_runs ALTER COLUMN task_id DROP NOT NULL"))
