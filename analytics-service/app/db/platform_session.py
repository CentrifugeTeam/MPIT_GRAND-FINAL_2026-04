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


def _migrate_nl_sql_jobs_max_rows() -> None:
    with _engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'nl_sql_jobs'
                  AND column_name = 'max_rows'
                """
            )
        ).fetchone()
        if row:
            return
    with _engine.begin() as conn:
        conn.execute(text("ALTER TABLE nl_sql_jobs ADD COLUMN max_rows INTEGER"))


def _has_column(table_name: str, column_name: str) -> bool:
    with _engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).fetchone()
        return bool(row)


def _migrate_nl_chat_sessions_team_fields() -> None:
    with _engine.begin() as conn:
        if not _has_column("nl_chat_sessions", "visibility"):
            conn.execute(text("ALTER TABLE nl_chat_sessions ADD COLUMN visibility VARCHAR(32)"))
            conn.execute(text("UPDATE nl_chat_sessions SET visibility='private' WHERE visibility IS NULL"))
            conn.execute(text("ALTER TABLE nl_chat_sessions ALTER COLUMN visibility SET DEFAULT 'private'"))
        if not _has_column("nl_chat_sessions", "created_by_user_id"):
            conn.execute(text("ALTER TABLE nl_chat_sessions ADD COLUMN created_by_user_id UUID"))
            conn.execute(
                text(
                    "UPDATE nl_chat_sessions SET created_by_user_id=user_id "
                    "WHERE created_by_user_id IS NULL"
                )
            )
        if not _has_column("nl_chat_sessions", "team_space_id"):
            conn.execute(text("ALTER TABLE nl_chat_sessions ADD COLUMN team_space_id UUID"))


def _migrate_nl_chat_invites_owner_email() -> None:
    with _engine.begin() as conn:
        if not _has_column("nl_chat_invites", "owner_invite_email"):
            conn.execute(
                text("ALTER TABLE nl_chat_invites ADD COLUMN owner_invite_email VARCHAR(255)")
            )


def init_platform_tables():
    from app.db.platform_base import PlatformBase
    from app.db.platform_models import (  # noqa: F401
        AnalyticsChatSuggestion,
        AnalyticsAccessPolicy,
        AnalyticsDataSource,
        NlChatAccess,
        NlChatInvite,
        NlChatMessage,
        NlChatSession,
        NlSqlJob,
    )
    from app.services.access_policy_store import (
        migrate_access_policies_table,
        seed_default_user_policy_if_empty,
    )

    migrate_access_policies_table()
    PlatformBase.metadata.create_all(bind=_engine)
    _migrate_nl_sql_jobs_user_id_to_uuid()
    _migrate_nl_sql_jobs_max_rows()
    _migrate_nl_chat_sessions_team_fields()
    _migrate_nl_chat_invites_owner_email()
    from app.services.data_sources_store import (
        seed_data_sources_if_empty,
        sync_analytics_sources_from_env,
    )

    seed_data_sources_if_empty()
    sync_analytics_sources_from_env()
    seed_default_user_policy_if_empty()
