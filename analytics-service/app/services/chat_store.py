"""Персистентные NL-чаты (сессии + сообщения) в platform DB."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import func, or_

from app.db.platform_models import NlChatMessage, NlChatSession
from app.db.platform_session import PlatformSessionLocal


def _uid(s: str) -> uuid.UUID:
    return uuid.UUID(str(s))


def create_empty_session(
    user_id: str,
    chat_type: str = "chat",
) -> str:
    cid = uuid.uuid4()
    uid = _uid(user_id)
    db = PlatformSessionLocal()
    try:
        db.add(
            NlChatSession(
                id=cid,
                user_id=uid,
                title=None,
                preview_text=None,
                chat_type="chat",
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
                    "chat_type": "chat",
                    "message_count": row.message_count or 0,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
            )
        return out, total
    finally:
        db.close()


def delete_messages_by_keys(
    user_id: str,
    conversation_id: str,
    keys: list[str],
    *,
    max_keys: int = 32,
) -> list[str]:
    """Удалить сообщения по pk (UUID) или по client_message_id. Возвращает id строк UI: client_message_id или str(pk)."""
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    cleaned: list[str] = []
    seen: set[str] = set()
    for k in keys:
        s = str(k).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        cleaned.append(s)
        if len(cleaned) >= max_keys:
            break
    if not cleaned:
        return []
    db = PlatformSessionLocal()
    try:
        sess = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if sess is None:
            raise ValueError("chat session not found")
        uuid_keys: list[uuid.UUID] = []
        for s in cleaned:
            try:
                uuid_keys.append(uuid.UUID(s))
            except ValueError:
                pass
        conds = []
        if uuid_keys:
            conds.append(NlChatMessage.id.in_(uuid_keys))
        conds.append(NlChatMessage.client_message_id.in_(cleaned))
        rows = (
            db.query(NlChatMessage)
            .filter(NlChatMessage.session_id == cid, or_(*conds))
            .all()
        )
        ui_seen: set[str] = set()
        ui_ids: list[str] = []
        for r in rows:
            cm = (r.client_message_id or "").strip()
            u = cm if cm else str(r.id)
            if u not in ui_seen:
                ui_seen.add(u)
                ui_ids.append(u)
            db.delete(r)
        remaining = (
            db.query(NlChatMessage).filter(NlChatMessage.session_id == cid).count()
        )
        sess.message_count = int(remaining)
        sess.updated_at = datetime.utcnow()
        db.commit()
        return ui_ids
    finally:
        db.close()


def delete_messages_from_anchor_inclusive(
    user_id: str,
    conversation_id: str,
    anchor_key: str,
) -> list[str]:
    """Удалить все сообщения сессии начиная с якоря (включительно) по порядку created_at."""
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    anchor = str(anchor_key).strip()
    if not anchor:
        return []
    db = PlatformSessionLocal()
    try:
        sess = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == uid)
            .one_or_none()
        )
        if sess is None:
            raise ValueError("chat session not found")
        rows = (
            db.query(NlChatMessage)
            .filter(NlChatMessage.session_id == cid)
            .order_by(NlChatMessage.created_at.asc())
            .all()
        )
        start_i: int | None = None
        for i, r in enumerate(rows):
            rid = str(r.id)
            cm = (r.client_message_id or "").strip()
            if rid == anchor or cm == anchor:
                start_i = i
                break
        if start_i is None:
            return []
        to_delete = rows[start_i:]
        ui_seen: set[str] = set()
        ui_ids: list[str] = []
        for r in to_delete:
            cm = (r.client_message_id or "").strip()
            u = cm if cm else str(r.id)
            if u not in ui_seen:
                ui_seen.add(u)
                ui_ids.append(u)
            db.delete(r)
        remaining = (
            db.query(NlChatMessage).filter(NlChatMessage.session_id == cid).count()
        )
        sess.message_count = int(remaining)
        sess.updated_at = datetime.utcnow()
        db.commit()
        return ui_ids
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
            "chat_type": "chat",
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    finally:
        db.close()
