"""ADMIN CRUD for analytics_access_policies."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.platform_session import PlatformSessionLocal
from app.services import access_policy_store as aps


def _require_admin(
    x_user_role: str | None = Header(
        None,
        alias="X-User-Role",
        description="Роль вызывающего; для этих маршрутов должна быть ADMIN",
    ),
) -> None:
    if (x_user_role or "").strip().upper() != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ADMIN only")


def get_db():
    db = PlatformSessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()


class AccessPolicyCreate(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "role_key": "USER",
                "source_key": "main-db",
                "allowed_tables": ["*"],
                "denied_columns": {"users": ["password_hash"]},
                "max_rows_override": None,
                "max_query_timeout_ms_override": None,
            }
        }
    }
    role_key: str = Field(..., max_length=64, description="Ключ роли из auth")
    source_key: str = Field(..., max_length=64, description="Ключ источника данных")
    allowed_tables: list[str] = Field(
        ...,
        description="Имена таблиц или ['*'] для всех разрешённых в источнике",
    )
    denied_columns: dict[str, list[str]] = Field(
        default_factory=dict,
        description='Запрещённые колонки: {"table": ["col", ...]}',
    )
    max_rows_override: int | None = Field(default=None, description="Переопределение лимита строк")
    max_query_timeout_ms_override: int | None = Field(
        default=None,
        description="Переопределение таймаута запроса (мс)",
    )


class AccessPolicyPatch(BaseModel):
    allowed_tables: list[str] | None = None
    denied_columns: dict[str, list[str]] | None = None
    max_rows_override: int | None = None
    max_query_timeout_ms_override: int | None = None


class AccessPolicyApi(BaseModel):
    id: str
    role_key: str
    source_key: str
    allowed_tables: list[str]
    denied_columns: dict[str, list[str]]
    max_rows_override: int | None
    max_query_timeout_ms_override: int | None

    model_config = {"from_attributes": False}


def _to_api(row: Any) -> AccessPolicyApi:
    return AccessPolicyApi(
        id=str(row.id),
        role_key=row.role_key,
        source_key=row.source_key,
        allowed_tables=list(row.allowed_tables or []),
        denied_columns=dict(row.denied_columns or {}),
        max_rows_override=row.max_rows_override,
        max_query_timeout_ms_override=row.max_query_timeout_ms_override,
    )


@router.get(
    "/access-policies",
    response_model=list[AccessPolicyApi],
    summary="Список политик доступа",
    description="Только ADMIN (заголовок X-User-Role).",
)
def list_access_policies(
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    return [_to_api(r) for r in aps.list_policies(db)]


@router.post(
    "/access-policies",
    response_model=AccessPolicyApi,
    status_code=status.HTTP_201_CREATED,
    summary="Создать политику",
    description="Пара (role_key, source_key) уникальна.",
)
def create_access_policy(
    body: AccessPolicyCreate,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    try:
        row = aps.create_policy(
            db,
            role_key=body.role_key,
            source_key=body.source_key,
            allowed_tables=body.allowed_tables,
            denied_columns=body.denied_columns,
            max_rows_override=body.max_rows_override,
            max_query_timeout_ms_override=body.max_query_timeout_ms_override,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return _to_api(row)


@router.patch(
    "/access-policies/{policy_id}",
    response_model=AccessPolicyApi,
    summary="Изменить политику",
)
def patch_access_policy(
    policy_id: str,
    body: AccessPolicyPatch,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    try:
        uid = uuid.UUID(policy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Invalid id") from e
    row = aps.update_policy(
        db,
        uid,
        allowed_tables=body.allowed_tables,
        denied_columns=body.denied_columns,
        max_rows_override=body.max_rows_override,
        max_query_timeout_ms_override=body.max_query_timeout_ms_override,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return _to_api(row)


@router.delete(
    "/access-policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить политику",
)
def delete_access_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    try:
        uid = uuid.UUID(policy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Invalid id") from e
    if not aps.delete_policy(db, uid):
        raise HTTPException(status_code=404, detail="Not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
