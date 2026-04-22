import uuid
from typing import Any

from app.db.platform_models import NlSqlJob
from app.db.platform_session import PlatformSessionLocal


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
