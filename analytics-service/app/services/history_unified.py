"""Объединённая история: классические nl_sql_jobs + NL-чаты."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.chat_store import list_chat_sessions_for_user
from app.services.job_store import list_jobs_for_user


def _job_to_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "entry_kind": "sql_job",
        "sort_at": row["created_at"],
        "job_id": row["job_id"],
        "user_id": row["user_id"],
        "question": row["question"],
        "max_rows": row.get("max_rows"),
        "template_key": row.get("template_key"),
        "status": row["status"],
        "sql": row.get("sql"),
        "explanation": row.get("explanation"),
        "error": row.get("error"),
        "result": row.get("result"),
        "created_at": row["created_at"],
        "updated_at": row.get("updated_at"),
        "conversation_id": None,
        "chat_title": None,
        "message_count": None,
    }


def _chat_to_item(row: dict[str, Any]) -> dict[str, Any]:
    st = row.get("updated_at") or row["created_at"]
    preview = (row.get("preview_text") or row.get("title") or "").strip()
    chat_type = str(row.get("chat_type") or "chat")
    return {
        "entry_kind": "report_task" if chat_type == "report" else "nl_chat",
        "sort_at": st,
        "conversation_id": row["conversation_id"],
        "user_id": row["user_id"],
        "question": preview[:500] if preview else "—",
        "chat_title": row.get("title"),
        "message_count": int(row.get("message_count") or 0),
        "created_at": row["created_at"],
        "updated_at": row.get("updated_at"),
        "chat_type": chat_type,
        "cron_expr": row.get("cron_expr"),
        "cron_timezone": row.get("cron_timezone"),
        "repeat_limit": row.get("repeat_limit"),
        "runs_count": row.get("runs_count"),
        "next_run_at": row.get("next_run_at"),
        "last_run_at": row.get("last_run_at"),
        "is_active": row.get("is_active"),
        "job_id": None,
        "max_rows": None,
        "template_key": None,
        "status": "ready",
        "sql": None,
        "explanation": None,
        "error": None,
        "result": None,
    }


def list_unified_history(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    jobs, total_jobs = list_jobs_for_user(user_id, limit=400, offset=0)
    chats, total_chats = list_chat_sessions_for_user(user_id, limit=400, offset=0)
    merged: list[dict[str, Any]] = []
    merged.extend(_job_to_item(j) for j in jobs)
    merged.extend(_chat_to_item(c) for c in chats)

    def _key(x: dict[str, Any]) -> datetime:
        v = x.get("sort_at")
        if isinstance(v, datetime):
            return v
        return datetime.min

    merged.sort(key=_key, reverse=True)
    total = int(total_jobs) + int(total_chats)
    sliced = merged[offset : offset + limit]
    return sliced, total
