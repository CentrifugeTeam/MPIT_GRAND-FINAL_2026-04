from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update

from app.db.models import ReportTaskTemplate
from app.db.session import SessionLocal


def _template_to_dict(row: ReportTaskTemplate) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "user_id": str(row.user_id),
        "title": row.title,
        "instruction": row.instruction,
        "analytics_source_key": row.analytics_source_key,
        "schedule_type": row.schedule_type,
        "timezone": row.timezone,
        "once_at": row.once_at,
        "daily_time": row.daily_time,
        "weekly_day": row.weekly_day,
        "weekly_time": row.weekly_time,
        "monthly_day": row.monthly_day,
        "monthly_time": row.monthly_time,
        "yearly_date_ddmm": row.yearly_date_ddmm,
        "yearly_time": row.yearly_time,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _schedule_columns(sc: dict[str, Any]) -> dict[str, Any]:
    return {
        "schedule_type": sc["schedule_type"],
        "timezone": sc.get("timezone") or "UTC",
        "once_at": sc.get("once_at"),
        "daily_time": sc.get("daily_time"),
        "weekly_day": sc.get("weekly_day"),
        "weekly_time": sc.get("weekly_time"),
        "monthly_day": sc.get("monthly_day"),
        "monthly_time": sc.get("monthly_time"),
        "yearly_date_ddmm": sc.get("yearly_date_ddmm"),
        "yearly_time": sc.get("yearly_time"),
    }


def create_template(user_id: str, body: dict[str, Any]) -> dict[str, Any]:
    sc = body["schedule"]
    cols = _schedule_columns(sc)
    with SessionLocal.begin() as db:
        row = ReportTaskTemplate(
            user_id=user_id,
            title=body["title"].strip(),
            instruction=body["instruction"].strip(),
            analytics_source_key=body["analytics_source_key"].strip(),
            **cols,
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        return _template_to_dict(row)


def list_templates(user_id: str, limit: int = 50, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    with SessionLocal() as db:
        total = (
            db.execute(
                select(func.count()).select_from(ReportTaskTemplate).where(ReportTaskTemplate.user_id == user_id)
            ).scalar_one()
        )
        rows = (
            db.execute(
                select(ReportTaskTemplate)
                .where(ReportTaskTemplate.user_id == user_id)
                .order_by(ReportTaskTemplate.created_at.desc(), ReportTaskTemplate.id.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [_template_to_dict(r) for r in rows], int(total)


def get_template(user_id: str, template_id: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        row = (
            db.execute(
                select(ReportTaskTemplate).where(
                    ReportTaskTemplate.user_id == user_id,
                    ReportTaskTemplate.id == template_id,
                )
            )
            .scalars()
            .first()
        )
        if not row:
            return None
        return _template_to_dict(row)


def patch_template(user_id: str, template_id: str, patch: dict[str, Any]) -> bool:
    values: dict[str, Any] = {}
    if "title" in patch:
        values["title"] = patch["title"].strip()
    if "instruction" in patch:
        values["instruction"] = patch["instruction"].strip()
    if "analytics_source_key" in patch:
        values["analytics_source_key"] = patch["analytics_source_key"].strip()
    if "schedule" in patch:
        values.update(_schedule_columns(patch["schedule"]))
    values["updated_at"] = datetime.now(UTC)
    with SessionLocal.begin() as db:
        res = db.execute(
            update(ReportTaskTemplate)
            .where(ReportTaskTemplate.id == template_id, ReportTaskTemplate.user_id == user_id)
            .values(**values)
        )
        return bool(res.rowcount)


def delete_template(user_id: str, template_id: str) -> bool:
    with SessionLocal.begin() as db:
        res = db.execute(
            delete(ReportTaskTemplate).where(
                ReportTaskTemplate.id == template_id,
                ReportTaskTemplate.user_id == user_id,
            )
        )
        return bool(res.rowcount)
