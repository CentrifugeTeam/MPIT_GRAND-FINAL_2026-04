"""Проверка покрытия системных шаблонов в той же platform DB, что и report-task-service."""

from __future__ import annotations

from sqlalchemy import text

from app.db.platform_session import platform_engine


def count_distinct_system_schedule_types(analytics_source_key: str) -> int:
    key = (analytics_source_key or "").strip()
    if not key:
        return 0
    eng = platform_engine()
    try:
        with eng.connect() as conn:
            n = conn.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT schedule_type)::int
                    FROM report_task_templates
                    WHERE is_system = TRUE
                      AND analytics_source_key = :k
                      AND schedule_type IN ('once', 'daily', 'weekly', 'monthly', 'yearly')
                    """
                ),
                {"k": key},
            ).scalar()
        return int(n or 0)
    except Exception:
        return 0
