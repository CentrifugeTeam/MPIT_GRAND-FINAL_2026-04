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
    from app.db.models import ReportRun, ReportTask, ReportTaskTemplate  # noqa: F401

    PlatformBase.metadata.create_all(bind=_engine)
    _migrate_report_tasks_weekly_schema()
    _migrate_report_runs_schema()
    _migrate_report_task_templates_system()


def _migrate_report_tasks_weekly_schema() -> None:
    with _engine.connect() as conn:
        weekly_day_col = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='report_tasks'
                  AND column_name='weekly_day'
                """
            )
        ).fetchone()
        weekly_time_col = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='report_tasks'
                  AND column_name='weekly_time'
                """
            )
        ).fetchone()
    with _engine.begin() as conn:
        if not weekly_day_col:
            conn.execute(text("ALTER TABLE report_tasks ADD COLUMN weekly_day INTEGER"))
        if not weekly_time_col:
            conn.execute(text("ALTER TABLE report_tasks ADD COLUMN weekly_time VARCHAR(8)"))


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


def _migrate_report_task_templates_system() -> None:
    with _engine.connect() as conn:
        col = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='report_task_templates'
                  AND column_name='is_system'
                """
            )
        ).fetchone()
        idx = conn.execute(
            text(
                """
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND indexname = 'uq_report_task_templates_system_key_schedule'
                """
            )
        ).fetchone()
    with _engine.begin() as conn:
        if not col:
            conn.execute(
                text(
                    "ALTER TABLE report_task_templates ADD COLUMN is_system BOOLEAN NOT NULL DEFAULT FALSE"
                )
            )
        if not idx:
            conn.execute(
                text(
                    """
                    CREATE UNIQUE INDEX uq_report_task_templates_system_key_schedule
                    ON report_task_templates (analytics_source_key, schedule_type)
                    WHERE is_system = TRUE
                    """
                )
            )
