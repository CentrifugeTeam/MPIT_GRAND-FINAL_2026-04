"""Персистентные NL-чаты (сессии + сообщения) в platform DB."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import and_, func, insert, or_

from app.db.platform_models import NlChatAccess, NlChatInvite, NlChatMessage, NlChatSession
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
                created_by_user_id=uid,
                visibility="private",
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
                    created_by_user_id=uid,
                    visibility="private",
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
        own_q = db.query(NlChatSession).filter(NlChatSession.user_id == uid)
        shared_q = (
            db.query(NlChatSession)
            .join(
                NlChatAccess,
                and_(
                    NlChatAccess.conversation_id == NlChatSession.id,
                    NlChatAccess.user_id == uid,
                ),
            )
            .filter(NlChatSession.user_id != uid)
        )
        rows_map: dict[str, NlChatSession] = {}
        for row in own_q.all():
            rows_map[str(row.id)] = row
        for row in shared_q.all():
            rows_map[str(row.id)] = row
        rows = sorted(
            rows_map.values(),
            key=lambda x: x.updated_at or x.created_at,
            reverse=True,
        )
        total = len(rows)
        rows = rows[offset : offset + limit]
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "conversation_id": str(row.id),
                    "user_id": str(row.user_id),
                    "title": row.title,
                    "preview_text": row.preview_text,
                    "chat_type": "chat",
                    "access_role": "owner" if row.user_id == uid else "viewer",
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
            .filter(NlChatSession.id == cid)
            .one_or_none()
        )
        if sess is None:
            return []
        if sess.user_id != uid:
            allowed = (
                db.query(NlChatAccess)
                .filter(
                    NlChatAccess.conversation_id == cid,
                    NlChatAccess.user_id == uid,
                )
                .one_or_none()
            )
            if allowed is None:
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
        row = db.query(NlChatSession).filter(NlChatSession.id == cid).one_or_none()
        if row is None:
            return None
        access_role = "owner"
        if row.user_id != uid:
            access = (
                db.query(NlChatAccess)
                .filter(
                    NlChatAccess.conversation_id == cid,
                    NlChatAccess.user_id == uid,
                )
                .one_or_none()
            )
            if access is None:
                return None
            access_role = access.access_role or "viewer"
        return {
            "conversation_id": str(row.id),
            "title": row.title,
            "preview_text": row.preview_text,
            "chat_type": "chat",
            "access_role": access_role,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    finally:
        db.close()


def user_can_write_chat(user_id: str, conversation_id: str) -> bool:
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        row = db.query(NlChatSession).filter(NlChatSession.id == cid).one_or_none()
        if row is None:
            return False
        return row.user_id == uid
    finally:
        db.close()


def create_chat_invites(
    owner_user_id: str,
    conversation_id: str,
    emails: list[str],
    *,
    owner_email: str | None = None,
) -> list[dict[str, Any]]:
    owner_uid = _uid(owner_user_id)
    cid = _uid(conversation_id)
    owner_mail = (owner_email or "").strip().lower() or None
    db = PlatformSessionLocal()
    try:
        session = (
            db.query(NlChatSession)
            .filter(NlChatSession.id == cid, NlChatSession.user_id == owner_uid)
            .one_or_none()
        )
        if session is None:
            raise ValueError("chat session not found")
        chat_title = (session.title or session.preview_text or "").strip() or None
        created: list[dict[str, Any]] = []
        for email in emails:
            e = str(email or "").strip().lower()
            if not e or "@" not in e:
                continue
            inv = NlChatInvite(
                conversation_id=cid,
                owner_user_id=owner_uid,
                invitee_email=e,
                owner_invite_email=owner_mail,
                access_mode="view_only",
                status="pending",
            )
            db.add(inv)
            db.flush()
            created.append(
                {
                    "invite_id": str(inv.id),
                    "conversation_id": str(inv.conversation_id),
                    "owner_user_id": str(owner_uid),
                    "owner_email": owner_mail,
                    "invitee_email": inv.invitee_email,
                    "chat_title": chat_title,
                    "status": inv.status,
                    "created_at": inv.created_at,
                }
            )
        db.commit()
        return created
    finally:
        db.close()


def list_incoming_invites(user_email: str, user_id: str | None = None) -> list[dict[str, Any]]:
    """Входящие pending по email + принятые по invitee_user_id (для блока «совместные чаты»)."""
    email = (user_email or "").strip().lower()
    uid = _uid(user_id) if user_id else None
    db = PlatformSessionLocal()
    try:
        if uid is not None:
            q = db.query(NlChatInvite).filter(
                or_(
                    and_(
                        NlChatInvite.status == "pending",
                        NlChatInvite.invitee_email == email,
                    ),
                    and_(
                        NlChatInvite.status == "accepted",
                        NlChatInvite.invitee_user_id == uid,
                    ),
                )
            )
        else:
            q = db.query(NlChatInvite).filter(
                NlChatInvite.status == "pending",
                NlChatInvite.invitee_email == email,
            )
        rows = q.order_by(
            func.coalesce(NlChatInvite.accepted_at, NlChatInvite.created_at).desc()
        ).all()
        out: list[dict[str, Any]] = []
        for row in rows:
            sess = (
                db.query(NlChatSession)
                .filter(NlChatSession.id == row.conversation_id)
                .one_or_none()
            )
            title = None
            if sess is not None:
                title = (sess.title or sess.preview_text or "").strip() or None
            own_mail = getattr(row, "owner_invite_email", None) or None
            if isinstance(own_mail, str):
                own_mail = own_mail.strip().lower() or None
            out.append(
                {
                    "invite_id": str(row.id),
                    "conversation_id": str(row.conversation_id),
                    "owner_user_id": str(row.owner_user_id),
                    "owner_email": own_mail,
                    "invitee_email": row.invitee_email,
                    "chat_title": title,
                    "status": row.status,
                    "created_at": row.created_at,
                    "is_for_current_user": bool(uid is not None),
                }
            )
        return out
    finally:
        db.close()


def _clone_chat_for_user(db, source_session: NlChatSession, user_uuid: uuid.UUID) -> str:
    """Копия сессии + сообщений для другого пользователя.

    Сообщения вставляем через Core ``insert().values(...)`` по одной строке: batched ORM-insert
    (insertmanyvalues) в SQLAlchemy 2.0 в сочетании с новой сессией давал FK violation на
    ``session_id`` (в БД уходил не тот UUID).
    """
    clone_id = uuid.uuid4()
    new_sess = NlChatSession(
        id=clone_id,
        user_id=user_uuid,
        created_by_user_id=source_session.created_by_user_id or source_session.user_id,
        visibility="private",
        title=source_session.title,
        preview_text=source_session.preview_text,
        chat_type=source_session.chat_type,
        message_count=0,
    )
    db.add(new_sess)
    db.flush()

    rows = (
        db.query(NlChatMessage)
        .filter(NlChatMessage.session_id == source_session.id)
        .order_by(NlChatMessage.created_at.asc())
        .all()
    )
    msg_table = NlChatMessage.__table__
    for row in rows:
        payload_val = (
            row.payload
            if isinstance(row.payload, dict)
            else dict(row.payload or {})
        )
        db.execute(
            insert(msg_table).values(
                id=uuid.uuid4(),
                session_id=clone_id,
                role=row.role,
                client_message_id=row.client_message_id,
                payload=payload_val,
                created_at=row.created_at,
            )
        )
    new_sess.message_count = len(rows)
    return str(clone_id)


def accept_chat_invite(invite_id: str, user_id: str, user_email: str) -> dict[str, Any]:
    iid = _uid(invite_id)
    uid = _uid(user_id)
    email = (user_email or "").strip().lower()
    db = PlatformSessionLocal()
    try:
        invite = db.query(NlChatInvite).filter(NlChatInvite.id == iid).one_or_none()
        if invite is None or invite.status != "pending":
            raise ValueError("invite not found")
        if invite.invitee_email.strip().lower() != email:
            raise PermissionError("invite belongs to another user")
        session = (
            db.query(NlChatSession).filter(NlChatSession.id == invite.conversation_id).one_or_none()
        )
        if session is None:
            raise ValueError("chat session not found")
        result_conversation_id = str(session.id)
        existing = (
            db.query(NlChatAccess)
            .filter(
                NlChatAccess.conversation_id == invite.conversation_id,
                NlChatAccess.user_id == uid,
            )
            .one_or_none()
        )
        if existing is None:
            db.add(
                NlChatAccess(
                    conversation_id=invite.conversation_id,
                    owner_user_id=invite.owner_user_id,
                    user_id=uid,
                    access_role="viewer",
                )
            )
        invite.status = "accepted"
        invite.invitee_user_id = uid
        invite.accepted_at = datetime.utcnow()
        db.commit()
        return {
            "invite_id": str(invite.id),
            "conversation_id": result_conversation_id,
            "status": invite.status,
        }
    finally:
        db.close()


def reject_chat_invite(invite_id: str, user_id: str, user_email: str) -> dict[str, Any]:
    iid = _uid(invite_id)
    email = (user_email or "").strip().lower()
    db = PlatformSessionLocal()
    try:
        invite = db.query(NlChatInvite).filter(NlChatInvite.id == iid).one_or_none()
        if invite is None or invite.status != "pending":
            raise ValueError("invite not found")
        if invite.invitee_email.strip().lower() != email:
            raise PermissionError("invite belongs to another user")
        invite.status = "rejected"
        db.commit()
        return {"invite_id": str(invite.id), "status": "rejected"}
    finally:
        db.close()


def clone_shared_chat_for_viewer(user_id: str, conversation_id: str) -> dict[str, Any]:
    """Клон для пользователя с доступом viewer (не владельца сессии)."""
    uid = _uid(user_id)
    cid = _uid(conversation_id)
    db = PlatformSessionLocal()
    try:
        session = (
            db.query(NlChatSession).filter(NlChatSession.id == cid).one_or_none()
        )
        if session is None:
            raise ValueError("chat session not found")
        if session.user_id == uid:
            raise PermissionError("owner should use their own chat, not clone")
        access = (
            db.query(NlChatAccess)
            .filter(NlChatAccess.conversation_id == cid, NlChatAccess.user_id == uid)
            .one_or_none()
        )
        if access is None:
            raise PermissionError("no viewer access to this chat")
        new_id = _clone_chat_for_user(db, session, uid)
        db.commit()
        return {"conversation_id": new_id}
    finally:
        db.close()
