"""Персистентные NL-чаты (сессии + сообщения) в platform DB."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func

from app.db.platform_models import NlChatMessage, NlChatSession
from app.db.platform_session import PlatformSessionLocal


def _uid(s: str) -> uuid.UUID:
    return uuid.UUID(str(s))


def _normalize_report_schedule(schedule: dict[str, Any] | None) -> dict[str, Any]:
    if not schedule:
        return {
            "cron_expr": None,
            "cron_timezone": None,
            "repeat_limit": None,
            "next_run_at": None,
            "is_active": True,
        }
    cron_expr = str(schedule.get("cron_expr") or "").strip()
    cron_timezone = str(schedule.get("cron_timezone") or "UTC").strip() or "UTC"
    if not cron_expr:
        raise ValueError("cron_expr required for report schedule")
    trigger = CronTrigger.from_crontab(cron_expr, timezone=cron_timezone)
    next_run_at = trigger.get_next_fire_time(None, datetime.now(trigger.timezone))
    repeat_limit = schedule.get("repeat_limit")
    if repeat_limit is not None:
        repeat_limit = int(repeat_limit)
        if repeat_limit < 1:
            raise ValueError("repeat_limit must be >= 1")
    return {
        "cron_expr": cron_expr,
        "cron_timezone": cron_timezone,
        "repeat_limit": repeat_limit,
        "next_run_at": next_run_at,
        "is_active": bool(schedule.get("is_active", True)),
    }


def create_empty_session(
    user_id: str,
    chat_type: str = "chat",
    schedule: dict[str, Any] | None = None,
    notification_email: str | None = None,
) -> str:
    email = str(notification_email or "").strip() or None
    cid = uuid.uuid4()
    uid = _uid(user_id)
    ctype = str(chat_type or "chat").strip().lower() or "chat"
    if ctype not in ("chat", "report"):
        raise ValueError("chat_type must be one of: chat, report")
    schedule_norm = _normalize_report_schedule(schedule) if ctype == "report" else None
    db = PlatformSessionLocal()
    try:
        db.add(
            NlChatSession(
                id=cid,
                user_id=uid,
                title=None,
                preview_text=None,
                chat_type=ctype,
                cron_expr=(schedule_norm or {}).get("cron_expr"),
                cron_timezone=(schedule_norm or {}).get("cron_timezone"),
                repeat_limit=(schedule_norm or {}).get("repeat_limit"),
                runs_count=0,
                next_run_at=(schedule_norm or {}).get("next_run_at"),
                last_run_at=None,
                is_active=(schedule_norm or {}).get("is_active", True),
                notification_email=email,
                message_count=0,
            )
        )
        db.commit()
        return str(cid)
    finally:
        db.close()


def ensure_session(user_id: str, conversation_id: str, title_hint: str | None = None) -> None:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        row = db.query(NlChatSession).filter(NlChatSession.id == cid).one_or_none()
        if row is None:
            hint = (title_hint or "").strip()[:200] or None
            db.add(
                NlChatSession(
                    id=cid,
                    user_id=uid,
                    title=hint,
                    preview_text=hint,
                    message_count=0,
                )
            )
            db.commit()
        elif row.user_id != uid:
            raise PermissionError("conversation belongs to another user")
        else:
            hint = (title_hint or "").strip()[:200]
            if hint:
                if not (row.preview_text or "").strip():
                    row.preview_text = hint[:500]
                tn = (row.title or "").strip()
                if not tn or len(tn) < 2:
                    row.title = hint[:120]
                row.updated_at = datetime.utcnow()
                db.commit()
    finally:
        db.close()


def append_message(
    user_id: str,
    conversation_id: str,
    role: str,
    payload: dict[str, Any],
    client_message_id: str | None = None,
) -> uuid.UUID:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        sess = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if sess is None:
            raise ValueError("chat session not found")
        mid = uuid.uuid4()
        db.add(
            NlChatMessage(
                id=mid,
                session_id=cid,
                role=role,
                client_message_id=client_message_id,
                payload=payload,
            )
        )
        sess.message_count = int(sess.message_count or 0) + 1
        sess.updated_at = datetime.utcnow()
        if role == "user" and isinstance(payload.get("text"), str):
            t = payload["text"].strip()
            if t and not (sess.preview_text or "").strip():
                sess.preview_text = t[:500]
            if t:
                cur = (sess.title or "").strip()
                if not cur or len(cur) < 2:
                    sess.title = t[:120]
        db.commit()
        return mid
    finally:
        db.close()


def list_chat_sessions_for_user(
    user_id: str,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    uid = _uid(user_id)
    db = PlatformSessionLocal()
    try:
        q = db.query(NlChatSession).filter(NlChatSession.user_id == uid)
        total = q.count()
        rows = (
            q.order_by(
                func.coalesce(NlChatSession.updated_at, NlChatSession.created_at).desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "conversation_id": str(row.id),
                    "user_id": str(row.user_id),
                    "title": row.title,
                    "preview_text": row.preview_text,
                    "chat_type": row.chat_type or "chat",
                    "cron_expr": row.cron_expr,
                    "cron_timezone": row.cron_timezone,
                    "repeat_limit": row.repeat_limit,
                    "runs_count": int(row.runs_count or 0),
                    "next_run_at": row.next_run_at,
                    "last_run_at": row.last_run_at,
                    "is_active": bool(row.is_active),
                    "notification_email": row.notification_email,
                    "message_count": row.message_count or 0,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
            )
        return out, total
    finally:
        db.close()


def list_messages(user_id: str, conversation_id: str) -> list[dict[str, Any]]:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        sess = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if sess is None:
            return []
        rows = (
            db.query(NlChatMessage)
            .filter(NlChatMessage.session_id == cid)
            .order_by(NlChatMessage.created_at.asc())
            .all()
        )
        return [
            {
                "id": str(r.id),
                "role": r.role,
                "payload": dict(r.payload or {}),
                "created_at": r.created_at,
                "client_message_id": r.client_message_id,
            }
            for r in rows
        ]
    finally:
        db.close()


def update_session_title(user_id: str, conversation_id: str, title: str) -> bool:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if row is None:
            return False
        row.title = title.strip()[:500] or row.title
        row.updated_at = datetime.utcnow()
        db.commit()
        return True
    finally:
        db.close()


def update_report_session(
    user_id: str,
    conversation_id: str,
    *,
    title: str | None = None,
    schedule: dict[str, Any] | None = None,
) -> bool:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if row is None or (row.chat_type or "chat") != "report":
            return False
        if title is not None and title.strip():
            row.title = title.strip()[:500]
        if schedule is not None:
            sch = _normalize_report_schedule(schedule)
            row.cron_expr = sch["cron_expr"]
            row.cron_timezone = sch["cron_timezone"]
            row.repeat_limit = sch["repeat_limit"]
            row.next_run_at = sch["next_run_at"]
            row.is_active = sch["is_active"]
        row.updated_at = datetime.utcnow()
        db.commit()
        return True
    finally:
        db.close()


def delete_session(user_id: str, conversation_id: str) -> bool:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if row is None:
            return False
        db.delete(row)
        db.commit()
        return True
    finally:
        db.close()


def delete_all_sessions_for_user(user_id: str) -> int:
    uid = _uid(user_id)
    db = PlatformSessionLocal()
    try:
        deleted = (
            db.query(NlChatSession)
            .filter(NlChatSession.user_id == uid)
            .delete(synchronize_session=False)
        )
        db.commit()
        return int(deleted or 0)
    finally:
        db.close()


def get_session_for_user(user_id: str, conversation_id: str) -> Optional[dict[str, Any]]:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if row is None:
            return None
        return {
            "conversation_id": str(row.id),
            "title": row.title,
            "preview_text": row.preview_text,
            "chat_type": row.chat_type or "chat",
            "cron_expr": row.cron_expr,
            "cron_timezone": row.cron_timezone,
            "repeat_limit": row.repeat_limit,
            "runs_count": int(row.runs_count or 0),
            "next_run_at": row.next_run_at,
            "last_run_at": row.last_run_at,
            "is_active": bool(row.is_active),
            "notification_email": row.notification_email,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    finally:
        db.close()


def reserve_due_report_sessions(limit: int = 100) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    db = PlatformSessionLocal()
    try:
        rows = (
            db.query(NlChatSession)
            .filter(
                NlChatSession.chat_type == "report",
                NlChatSession.is_active.is_(True),
                NlChatSession.cron_expr.isnot(None),
                NlChatSession.next_run_at.isnot(None),
                NlChatSession.next_run_at <= now,
            )
            .order_by(NlChatSession.next_run_at.asc())
            .limit(limit)
            .all()
        )
        out: list[dict[str, Any]] = []
        for row in rows:
            if row.repeat_limit is not None and int(row.runs_count or 0) >= int(row.repeat_limit):
                row.is_active = False
                continue
            cron_expr = str(row.cron_expr or "").strip()
            cron_timezone = str(row.cron_timezone or "UTC").strip() or "UTC"
            trigger = CronTrigger.from_crontab(cron_expr, timezone=cron_timezone)
            next_run_at = trigger.get_next_fire_time(None, datetime.now(trigger.timezone))
            row.runs_count = int(row.runs_count or 0) + 1
            row.last_run_at = now
            row.next_run_at = next_run_at
            if row.repeat_limit is not None and int(row.runs_count or 0) >= int(row.repeat_limit):
                row.is_active = False
            row.updated_at = now
            out.append(
                {
                    "conversation_id": str(row.id),
                    "user_id": str(row.user_id),
                    "title": row.title,
                    "preview_text": row.preview_text,
                    "runs_count": int(row.runs_count or 0),
                    "next_run_at": row.next_run_at,
                    "last_run_at": row.last_run_at,
                    "cron_expr": row.cron_expr,
                    "cron_timezone": row.cron_timezone,
                    "is_active": bool(row.is_active),
                    "notification_email": row.notification_email,
                }
            )
        db.commit()
        return out
    finally:
        db.close()
