import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.platform_base import PlatformBase


class NlSqlJob(PlatformBase):
    __tablename__ = "nl_sql_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    question = Column(Text, nullable=False)
    max_rows = Column(Integer, nullable=True)
    template_key = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    sql = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    result_payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NlChatSession(PlatformBase):
    __tablename__ = "nl_chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(Text, nullable=True)
    preview_text = Column(Text, nullable=True)
    chat_type = Column(String(32), nullable=False, default="chat")
    cron_expr = Column(String(255), nullable=True)
    cron_timezone = Column(String(64), nullable=True)
    repeat_limit = Column(Integer, nullable=True)
    runs_count = Column(Integer, nullable=False, default=0)
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    notification_email = Column(String(255), nullable=True)
    message_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalyticsAccessPolicy(PlatformBase):
    """Per-role, per-source allowlist of tables + denied columns (JSONB)."""

    __tablename__ = "analytics_access_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_key = Column(String(64), nullable=False, index=True)
    source_key = Column(String(64), nullable=False, index=True)
    allowed_tables = Column(JSONB, nullable=False)
    denied_columns = Column(JSONB, nullable=False, server_default="{}")
    max_rows_override = Column(Integer, nullable=True)
    max_query_timeout_ms_override = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalyticsDataSource(PlatformBase):
    """Подключаемые БД для SELECT (NL→SQL). Ключ — в payload / query source_key."""

    __tablename__ = "analytics_data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_key = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    database_url = Column(Text, nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NlChatMessage(PlatformBase):
    __tablename__ = "nl_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nl_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(16), nullable=False)
    client_message_id = Column(String(128), nullable=True)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
