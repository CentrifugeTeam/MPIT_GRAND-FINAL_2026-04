import json
import uuid
from typing import Any, Optional

from sqlalchemy import create_engine, text

from app.core.config import get_settings


def update_job_row(
    job_id: uuid.UUID,
    status: str,
    sql: Optional[str] = None,
    explanation: Optional[str] = None,
    error: Optional[str] = None,
    result_payload: Optional[dict[str, Any]] = None,
) -> None:
    settings = get_settings()
    engine = create_engine(settings.PLATFORM_DATABASE_URL, pool_pre_ping=True)

    if status == "processing":
        with engine.connect() as conn:
            conn.execute(
                text(
                    "UPDATE nl_sql_jobs SET status = 'processing', updated_at = NOW() WHERE id = :id"
                ),
                {"id": job_id},
            )
            conn.commit()
        return

    if status == "error":
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    UPDATE nl_sql_jobs
                    SET status = :status,
                        error = :error,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {"status": status, "error": error or "", "id": job_id},
            )
            conn.commit()
        return

    rp = (
        json.dumps(result_payload, default=str)
        if result_payload is not None
        else None
    )
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                UPDATE nl_sql_jobs
                SET status = :status,
                    sql = :sql,
                    explanation = :explanation,
                    error = NULL,
                    result_payload = CAST(:rp AS jsonb),
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "status": status,
                "sql": sql,
                "explanation": explanation,
                "rp": rp,
                "id": job_id,
            },
        )
        conn.commit()
