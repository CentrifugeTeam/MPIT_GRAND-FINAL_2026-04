from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update, delete

from app.db.models import ReportRun
from app.db.session import SessionLocal


def _first_sentence_from_text(
    result_summary: str | None, query_text: str | None, max_len: int = 240
) -> str | None:
    raw = (result_summary or "").strip()
    if not raw:
        raw = (query_text or "").strip()
    if not raw:
        return None
    t = " ".join(raw.split())
    cut: int | None = None
    for i, ch in enumerate(t):
        if ch in ".!?…":
            if i == len(t) - 1 or t[i + 1] in " \n\t":
                cut = i + 1
                break
    if cut is not None:
        t = t[:cut].strip()
    elif "\n" in t:
        t = t.split("\n", 1)[0].strip()
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip()
        if not t.endswith("…"):
            t += "…"
    return t if t else None


def latest_done_report_sentence_by_task_ids(user_id: str, task_ids: list[str]) -> dict[str, str]:
    """Latest status=done run per task_id (by created_at desc); one short preview sentence."""
    if not task_ids:
        return {}
    uid = uuid.UUID(str(user_id))
    tid_uuids = [uuid.UUID(t) for t in task_ids]
    rn = (
        func.row_number()
        .over(partition_by=ReportRun.task_id, order_by=ReportRun.created_at.desc())
        .label("rn")
    )
    subq = (
        select(ReportRun.task_id, ReportRun.result_summary, ReportRun.query_text, rn)
        .where(
            ReportRun.user_id == uid,
            ReportRun.task_id.in_(tid_uuids),
            ReportRun.status == "done",
        )
    ).subquery()
    stmt = select(subq.c.task_id, subq.c.result_summary, subq.c.query_text).where(subq.c.rn == 1)
    out: dict[str, str] = {}
    with SessionLocal() as db:
        for row in db.execute(stmt).all():
            tid = str(row.task_id) if row.task_id else None
            if not tid:
                continue
            preview = _first_sentence_from_text(row.result_summary, row.query_text)
            if preview:
                out[tid] = preview
    return out


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


def mark_run_failed(
    report_id: str,
    error: str,
    result_summary: str | None = None,
    result_payload: dict[str, Any] | None = None,
) -> bool:
    summary = (result_summary or error or "").strip()
    if len(summary) > 2000:
        summary = summary[:1997].rstrip() + "..."
    with SessionLocal.begin() as db:
        res = db.execute(
            update(ReportRun)
            .where(ReportRun.id == report_id)
            .values(
                status="failed",
                error=error,
                result_summary=summary or "Не удалось сформировать отчёт из-за ошибки запроса.",
                result_payload=result_payload,
                finished_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        return bool(res.rowcount)
