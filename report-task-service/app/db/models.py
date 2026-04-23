import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import PlatformBase


class ReportTask(PlatformBase):
    __tablename__ = "report_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    instruction = Column(Text, nullable=False)
    analytics_source_key = Column(String(64), nullable=False)
    schedule_type = Column(String(16), nullable=False)
    once_at = Column(DateTime, nullable=True)
    daily_time = Column(String(8), nullable=True)
    weekly_day = Column(Integer, nullable=True)
    weekly_time = Column(String(8), nullable=True)
    monthly_day = Column(Integer, nullable=True)
    monthly_time = Column(String(8), nullable=True)
    yearly_date_ddmm = Column(String(5), nullable=True)
    yearly_time = Column(String(8), nullable=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    is_active = Column(Boolean, nullable=False, default=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    last_run_at = Column(DateTime, nullable=True)
    runs_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportTaskTemplate(PlatformBase):
    __tablename__ = "report_task_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    instruction = Column(Text, nullable=False)
    analytics_source_key = Column(String(64), nullable=False)
    schedule_type = Column(String(16), nullable=False)
    once_at = Column(DateTime, nullable=True)
    daily_time = Column(String(8), nullable=True)
    weekly_day = Column(Integer, nullable=True)
    weekly_time = Column(String(8), nullable=True)
    monthly_day = Column(Integer, nullable=True)
    monthly_time = Column(String(8), nullable=True)
    yearly_date_ddmm = Column(String(5), nullable=True)
    yearly_time = Column(String(8), nullable=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportRun(PlatformBase):
    __tablename__ = "report_runs"

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("report_tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    status = Column(String(16), nullable=False, default="pending")
    query_text = Column(Text, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)
    result_payload = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
