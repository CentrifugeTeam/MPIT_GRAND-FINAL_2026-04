import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
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
