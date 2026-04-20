import uuid
from typing import Any, Optional

from app.db.platform_models import NlSqlJob
from app.db.platform_session import PlatformSessionLocal


def create_job(
    user_id: str,
    question: str,
    template_key: Optional[str],
    job_id: Optional[uuid.UUID] = None,
    max_rows: Optional[int] = None,
) -> uuid.UUID:
    jid = job_id or uuid.uuid4()
    uid = uuid.UUID(user_id)
    db = PlatformSessionLocal()
    try:
        row = NlSqlJob(
            id=jid,
            user_id=uid,
            question=question,
            max_rows=max_rows,
            template_key=template_key,
            status="pending",
        )
        db.add(row)
        db.commit()
        return jid
    finally:
        db.close()


def update_job_status(
    job_id: uuid.UUID,
    status: str,
    sql: Optional[str] = None,
    explanation: Optional[str] = None,
    error: Optional[str] = None,
    result_payload: Optional[dict[str, Any]] = None,
) -> None:
    db = PlatformSessionLocal()
    try:
        row = db.query(NlSqlJob).filter(NlSqlJob.id == job_id).one_or_none()
        if row:
            row.status = status
            if sql is not None:
                row.sql = sql
            if explanation is not None:
                row.explanation = explanation
            if error is not None:
                row.error = error
            if result_payload is not None:
                row.result_payload = result_payload
            db.commit()
    finally:
        db.close()


def reset_job_for_rerun(
    job_id: uuid.UUID,
    user_id: str,
    question: str,
    template_key: Optional[str],
    max_rows: Optional[int] = None,
) -> bool:
    uid = uuid.UUID(user_id)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(NlSqlJob)
            .filter(NlSqlJob.id == job_id, NlSqlJob.user_id == uid)
            .one_or_none()
        )
        if row is None:
            return False
        row.question = question
        row.max_rows = max_rows
        row.template_key = template_key
        row.status = "pending"
        row.sql = None
        row.explanation = None
        row.error = None
        row.result_payload = None
        db.commit()
        return True
    finally:
        db.close()


def get_job(job_id: uuid.UUID, user_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    db = PlatformSessionLocal()
    try:
        q = db.query(NlSqlJob).filter(NlSqlJob.id == job_id)
        if user_id:
            q = q.filter(NlSqlJob.user_id == uuid.UUID(user_id))
        row = q.one_or_none()
        if not row:
            return None
        return {
            "job_id": str(row.id),
            "user_id": str(row.user_id),
            "question": row.question,
            "max_rows": row.max_rows,
            "template_key": row.template_key,
            "status": row.status,
            "sql": row.sql,
            "explanation": row.explanation,
            "error": row.error,
            "result": row.result_payload,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    finally:
        db.close()


def list_jobs_for_user(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    uid = uuid.UUID(user_id)
    db = PlatformSessionLocal()
    try:
        q = db.query(NlSqlJob).filter(NlSqlJob.user_id == uid)
        total = q.count()
        rows = (
            q.order_by(NlSqlJob.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "job_id": str(row.id),
                    "user_id": str(row.user_id),
                    "question": row.question,
                    "max_rows": row.max_rows,
                    "template_key": row.template_key,
                    "status": row.status,
                    "sql": row.sql,
                    "explanation": row.explanation,
                    "error": row.error,
                    "result": row.result_payload,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
            )
        return out, total
    finally:
        db.close()


def delete_all_jobs_for_user(user_id: str) -> int:
    uid = uuid.UUID(user_id)
    db = PlatformSessionLocal()
    try:
        deleted = (
            db.query(NlSqlJob).filter(NlSqlJob.user_id == uid).delete(synchronize_session=False)
        )
        db.commit()
        return int(deleted or 0)
    finally:
        db.close()


def delete_job(job_id: uuid.UUID, user_id: str) -> bool:
    uid = uuid.UUID(user_id)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(NlSqlJob)
            .filter(NlSqlJob.id == job_id, NlSqlJob.user_id == uid)
            .one_or_none()
        )
        if row is None:
            return False
        db.delete(row)
        db.commit()
        return True
    finally:
        db.close()
