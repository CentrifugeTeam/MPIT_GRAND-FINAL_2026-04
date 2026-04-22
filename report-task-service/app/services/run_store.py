from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update, delete

from app.db.models import ReportRun
from app.db.session import SessionLocal


def _run_to_dict(row: ReportRun) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "task_id": str(row.task_id) if row.task_id else None,
        "user_id": str(row.user_id),
        "status": row.status,
        "query_text": row.query_text,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "error": row.error,
        "result_summary": row.result_summary,
        "result_payload": row.result_payload,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def create_run(task_id: str, user_id: str, query_text: str) -> dict[str, Any]:
    now = datetime.now(UTC)
    with SessionLocal.begin() as db:
        row = ReportRun(
            user_id=user_id,
            task_id=task_id,
            status="running",
            query_text=query_text,
            started_at=now,
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        return _run_to_dict(row)


def list_runs(task_id: str, limit: int = 50, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    with SessionLocal() as db:
        total = (
            db.execute(select(func.count()).select_from(ReportRun).where(ReportRun.task_id == task_id))
            .scalar_one()
        )
        rows = (
            db.execute(
                select(ReportRun)
                .where(ReportRun.task_id == task_id)
                .order_by(ReportRun.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [_run_to_dict(r) for r in rows], int(total)


def list_runs_for_user(user_id: str, limit: int = 50, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
    with SessionLocal() as db:
        total = (
            db.execute(select(func.count()).select_from(ReportRun).where(ReportRun.user_id == user_id))
            .scalar_one()
        )
        rows = (
            db.execute(
                select(ReportRun)
                .where(ReportRun.user_id == user_id)
                .order_by(ReportRun.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [_run_to_dict(r) for r in rows], int(total)


def get_run(report_id: str) -> dict[str, Any] | None:
    with SessionLocal() as db:
        row = db.execute(select(ReportRun).where(ReportRun.id == report_id)).scalars().first()
        return _run_to_dict(row) if row else None


def create_manual_run(user_id: str, body: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(UTC)
    with SessionLocal.begin() as db:
        row = ReportRun(
            user_id=user_id,
            task_id=body.get("task_id"),
            status=body.get("status", "pending"),
            query_text=body["query_text"].strip(),
            started_at=body.get("started_at") or now,
            finished_at=body.get("finished_at"),
            error=body.get("error"),
            result_summary=body.get("result_summary"),
            result_payload=body.get("result_payload"),
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        return _run_to_dict(row)


def patch_run(user_id: str, report_id: str, patch: dict[str, Any]) -> bool:
    values = dict(patch)
    if "query_text" in values and isinstance(values["query_text"], str):
        values["query_text"] = values["query_text"].strip()
    values["updated_at"] = datetime.now(UTC)
    with SessionLocal.begin() as db:
        res = db.execute(
            update(ReportRun)
            .where(ReportRun.id == report_id, ReportRun.user_id == user_id)
            .values(**values)
        )
        return bool(res.rowcount)


def delete_run(user_id: str, report_id: str) -> bool:
    with SessionLocal.begin() as db:
        res = db.execute(
            delete(ReportRun).where(ReportRun.id == report_id, ReportRun.user_id == user_id)
        )
        return bool(res.rowcount)


def mark_run_done(report_id: str, result_summary: str | None, result_payload: dict[str, Any] | None) -> bool:
    with SessionLocal.begin() as db:
        res = db.execute(
            update(ReportRun)
            .where(ReportRun.id == report_id)
            .values(
                status="done",
                result_summary=result_summary,
                result_payload=result_payload,
                finished_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        return bool(res.rowcount)


def mark_run_failed(report_id: str, error: str) -> bool:
    with SessionLocal.begin() as db:
        res = db.execute(
            update(ReportRun)
            .where(ReportRun.id == report_id)
            .values(
                status="failed",
                error=error,
                finished_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        return bool(res.rowcount)
