"""CRUD for analytics_access_policies (platform DB)."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.platform_models import AnalyticsAccessPolicy
from app.services.access_policy import AccessPolicyView, admin_bypass, policy_view_from_row
from app.services.data_sources_store import get_default_source_key
from app.db.platform_session import PlatformSessionLocal


def list_policies(db: Session) -> list[AnalyticsAccessPolicy]:
    return db.query(AnalyticsAccessPolicy).order_by(
        AnalyticsAccessPolicy.role_key, AnalyticsAccessPolicy.source_key
    ).all()


def get_policy_row(
    db: Session, *, role_key: str, source_key: str
) -> Optional[AnalyticsAccessPolicy]:
    rk = role_key.strip().upper()
    sk = source_key.strip()
    return (
        db.query(AnalyticsAccessPolicy)
        .filter(
            AnalyticsAccessPolicy.role_key == rk,
            AnalyticsAccessPolicy.source_key == sk,
        )
        .first()
    )


def resolve_effective_policy(
    *,
    user_role: Optional[str],
    source_key: Optional[str],
    db: Session,
) -> Optional[AccessPolicyView]:
    """None if access denied (caller should 403). ADMIN → full allow synthetic view."""
    if admin_bypass(user_role):
        return AccessPolicyView(
            allowed_tables_lower=frozenset({"*"}),
            denied_columns={},
        )
    sk = (source_key or "").strip() or get_default_source_key()
    if not sk:
        return None
    rk = (user_role or "USER").strip().upper()
    row = get_policy_row(db, role_key=rk, source_key=sk)
    if not row and rk != "USER":
        row = get_policy_row(db, role_key="USER", source_key=sk)
    if not row:
        return None
    return policy_view_from_row(row.allowed_tables, row.denied_columns)


def policy_to_payload(policy: AccessPolicyView) -> dict[str, Any]:
    return {
        "allowed_tables": sorted(policy.allowed_tables_lower),
        "denied_columns": {k: sorted(v) for k, v in policy.denied_columns.items()},
    }


def create_policy(
    db: Session,
    *,
    role_key: str,
    source_key: str,
    allowed_tables: list[str],
    denied_columns: dict[str, list[str]],
    max_rows_override: Optional[int] = None,
    max_query_timeout_ms_override: Optional[int] = None,
) -> AnalyticsAccessPolicy:
    row = AnalyticsAccessPolicy(
        id=uuid.uuid4(),
        role_key=role_key.strip().upper(),
        source_key=source_key.strip(),
        allowed_tables=allowed_tables,
        denied_columns=denied_columns or {},
        max_rows_override=max_rows_override,
        max_query_timeout_ms_override=max_query_timeout_ms_override,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_policy(
    db: Session,
    policy_id: uuid.UUID,
    *,
    allowed_tables: Optional[list[str]] = None,
    denied_columns: Optional[dict[str, list[str]]] = None,
    max_rows_override: Optional[int] = None,
    max_query_timeout_ms_override: Optional[int] = None,
) -> Optional[AnalyticsAccessPolicy]:
    row = db.query(AnalyticsAccessPolicy).filter(AnalyticsAccessPolicy.id == policy_id).first()
    if not row:
        return None
    if allowed_tables is not None:
        row.allowed_tables = allowed_tables
    if denied_columns is not None:
        row.denied_columns = denied_columns
    if max_rows_override is not None:
        row.max_rows_override = max_rows_override
    if max_query_timeout_ms_override is not None:
        row.max_query_timeout_ms_override = max_query_timeout_ms_override
    db.commit()
    db.refresh(row)
    return row


def delete_policy(db: Session, policy_id: uuid.UUID) -> bool:
    row = db.query(AnalyticsAccessPolicy).filter(AnalyticsAccessPolicy.id == policy_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def seed_default_user_policy_if_empty() -> None:
    """Bootstrap USER + default source so NL works after deny-by-default."""
    with PlatformSessionLocal() as db:
        cnt = db.query(AnalyticsAccessPolicy).count()
        if cnt > 0:
            return
        sk = get_default_source_key()
        if not sk:
            return
        row = AnalyticsAccessPolicy(
            id=uuid.uuid4(),
            role_key="USER",
            source_key=sk,
            allowed_tables=["*"],
            denied_columns={},
            max_rows_override=None,
            max_query_timeout_ms_override=None,
        )
        db.add(row)
        db.commit()


def migrate_access_policies_table() -> None:
    from app.db.platform_session import platform_engine

    eng = platform_engine()
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS analytics_access_policies (
                    id UUID PRIMARY KEY,
                    role_key VARCHAR(64) NOT NULL,
                    source_key VARCHAR(64) NOT NULL,
                    allowed_tables JSONB NOT NULL,
                    denied_columns JSONB NOT NULL DEFAULT '{}',
                    max_rows_override INTEGER,
                    max_query_timeout_ms_override INTEGER,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    updated_at TIMESTAMPTZ,
                    UNIQUE (role_key, source_key)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS nl_query_audit (
                    id UUID PRIMARY KEY,
                    user_id VARCHAR(64),
                    user_role VARCHAR(64),
                    source_key VARCHAR(64),
                    question_redacted TEXT,
                    sql_text TEXT,
                    status VARCHAR(32),
                    guard_error TEXT,
                    planner_cost DOUBLE PRECISION,
                    duration_ms INTEGER,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
                """
            )
        )
