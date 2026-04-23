from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, text, update, delete

from app.db.models import ReportTask
from app.db.session import SessionLocal
from app.services import run_store
from app.services.schedule import calculate_next_run


def _task_to_dict(row: ReportTask) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "title": row.title,
        "instruction": row.instruction,
        "user_id": str(row.user_id),
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
        "is_active": row.is_active,
        "next_run_at": row.next_run_at,
        "last_run_at": row.last_run_at,
        "runs_count": row.runs_count,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "last_report_sentence": None,
    }


def create_task(user_id: str, body: dict[str, Any]) -> dict[str, Any]:
    sc = body["schedule"]
    next_run_at = calculate_next_run(
        sc["schedule_type"],
        timezone=sc.get("timezone"),
        once_at=sc.get("once_at"),
        daily_time=sc.get("daily_time"),
        weekly_day=sc.get("weekly_day"),
        weekly_time=sc.get("weekly_time"),
        monthly_day=sc.get("monthly_day"),
        monthly_time=sc.get("monthly_time"),
        yearly_date_ddmm=sc.get("yearly_date_ddmm"),
        yearly_time=sc.get("yearly_time"),
    )
    with SessionLocal.begin() as db:
        row = ReportTask(
            user_id=user_id,
            title=body["title"].strip(),
            instruction=body["instruction"].strip(),
            analytics_source_key=body["analytics_source_key"].strip(),
            schedule_type=sc["schedule_type"],
            timezone=sc.get("timezone") or "UTC",
            once_at=sc.get("once_at"),
            daily_time=sc.get("daily_time"),
            weekly_day=sc.get("weekly_day"),
            weekly_time=sc.get("weekly_time"),
            monthly_day=sc.get("monthly_day"),
            monthly_time=sc.get("monthly_time"),
            yearly_date_ddmm=sc.get("yearly_date_ddmm"),
            yearly_time=sc.get("yearly_time"),
            is_active=bool(body.get("is_active", True)),
            next_run_at=next_run_at if body.get("is_active", True) else None,
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        return _task_to_dict(row)


def list_tasks(user_id: str, limit: int = 50, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    with SessionLocal() as db:
        total = (
            db.execute(select(func.count()).select_from(ReportTask).where(ReportTask.user_id == user_id))
            .scalar_one()
        )
        rows = (
            db.execute(
                select(ReportTask)
                .where(ReportTask.user_id == user_id)
                .order_by(ReportTask.created_at.desc(), ReportTask.id.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        items = [_task_to_dict(r) for r in rows]
        ids = [d["id"] for d in items]
        previews = run_store.latest_done_report_sentence_by_task_ids(user_id, ids)
        for d in items:
            d["last_report_sentence"] = previews.get(d["id"])
        return items, int(total)


def get_task(user_id: str, task_id: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        row = (
            db.execute(
                select(ReportTask).where(
                    ReportTask.user_id == user_id,
                    ReportTask.id == task_id,
                )
            )
            .scalars()
            .first()
        )
        if not row:
            return None
        d = _task_to_dict(row)
        previews = run_store.latest_done_report_sentence_by_task_ids(user_id, [str(row.id)])
        d["last_report_sentence"] = previews.get(str(row.id))
        return d


def patch_task(user_id: str, task_id: str, patch: dict[str, Any]) -> bool:
    values: dict[str, Any] = {}
    if "title" in patch:
        values["title"] = patch["title"].strip()
    if "instruction" in patch:
        values["instruction"] = patch["instruction"].strip()
    if "analytics_source_key" in patch:
        values["analytics_source_key"] = patch["analytics_source_key"].strip()
    if "is_active" in patch:
        values["is_active"] = bool(patch["is_active"])
        if not values["is_active"]:
            values["next_run_at"] = None
    if "schedule" in patch:
        sc = patch["schedule"]
        values.update(
            {
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
        )
        values["next_run_at"] = calculate_next_run(
            sc["schedule_type"],
            timezone=sc.get("timezone"),
            once_at=sc.get("once_at"),
            daily_time=sc.get("daily_time"),
            weekly_day=sc.get("weekly_day"),
            weekly_time=sc.get("weekly_time"),
            monthly_day=sc.get("monthly_day"),
            monthly_time=sc.get("monthly_time"),
            yearly_date_ddmm=sc.get("yearly_date_ddmm"),
            yearly_time=sc.get("yearly_time"),
        )
        if "is_active" in values and not values["is_active"]:
            values["next_run_at"] = None
    values["updated_at"] = datetime.now(UTC)
    with SessionLocal.begin() as db:
        res = db.execute(
            update(ReportTask)
            .where(ReportTask.id == task_id, ReportTask.user_id == user_id)
            .values(**values)
        )
        return bool(res.rowcount)


def delete_task(user_id: str, task_id: str) -> bool:
    with SessionLocal.begin() as db:
        res = db.execute(
            delete(ReportTask).where(ReportTask.id == task_id, ReportTask.user_id == user_id)
        )
        return bool(res.rowcount)


def reserve_due_tasks(limit: int = 100) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    with SessionLocal.begin() as db:
        rows = db.execute(
            text(
                """
                SELECT id, user_id, instruction, analytics_source_key, schedule_type, timezone,
                       once_at, daily_time, weekly_day, weekly_time, monthly_day, monthly_time, yearly_date_ddmm, yearly_time,
                       runs_count
                FROM report_tasks
                WHERE is_active = TRUE
                  AND next_run_at IS NOT NULL
                  AND next_run_at <= :now
                ORDER BY next_run_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT :limit
                """
            ),
            {"now": now, "limit": limit},
        ).mappings().all()
        out = []
        for row in rows:
            next_run = calculate_next_run(
                row["schedule_type"],
                timezone=row["timezone"],
                once_at=row["once_at"],
                daily_time=row["daily_time"],
                weekly_day=row["weekly_day"],
                weekly_time=row["weekly_time"],
                monthly_day=row["monthly_day"],
                monthly_time=row["monthly_time"],
                yearly_date_ddmm=row["yearly_date_ddmm"],
                yearly_time=row["yearly_time"],
                now=now,
            )
            is_active = bool(next_run)
            db.execute(
                text(
                    """
                    UPDATE report_tasks
                    SET runs_count = runs_count + 1,
                        last_run_at = :now,
                        next_run_at = :next_run_at,
                        is_active = :is_active,
                        updated_at = :now
                    WHERE id = :task_id
                    """
                ),
                {
                    "now": now,
                    "next_run_at": next_run,
                    "is_active": is_active,
                    "task_id": row["id"],
                },
            )
            out.append(
                {
                    "task_id": str(row["id"]),
                    "user_id": str(row["user_id"]),
                    "instruction": row["instruction"],
                    "analytics_source_key": row["analytics_source_key"],
                }
            )
        return out
