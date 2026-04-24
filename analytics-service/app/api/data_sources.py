from typing import Optional

import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services import schema_cache
from app.services.analytics_db import dispose_analytics_engine_cache
from app.services.data_sources_store import (
    create_source,
    delete_source,
    list_sources_public,
    normalize_source_key,
    set_default_source,
    update_source,
)
from app.services.report_template_queue_consumer import publish_template_plan_request
from app.services.schema_scheduler import refresh_schema_cache

router = APIRouter()
logger = logging.getLogger(__name__)


def _require_write_token(x: Optional[str] = Header(None, alias="X-Analytics-Sources-Write-Token")) -> None:
    expected = (get_settings().ANALYTICS_SOURCES_WRITE_TOKEN or "").strip()
    if not expected:
        return
    if (x or "").strip() != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нужен корректный заголовок X-Analytics-Sources-Write-Token",
        )


class DataSourcePublic(BaseModel):
    key: str
    display_name: str
    is_default: bool


class DataSourcesListResponse(BaseModel):
    items: list[DataSourcePublic]
    default_key: str | None = None


class AllowedDataSourceKeysResponse(BaseModel):
    keys: list[str] = Field(
        default_factory=list,
        description="Источники, к которым у роли из X-User-Role есть политика доступа (или все для ADMIN)",
    )


class DataSourceCreateBody(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "key": "main-db",
        "display_name": "Warehouse (main_db)",
        "database_url": "postgresql://postgres:postgres@main-db:5432/main_db",
        "set_as_default": True
    }}}
    key: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field("", max_length=255)
    database_url: str = Field(..., min_length=8)
    set_as_default: bool = False


class DataSourcePatchBody(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "display_name": "Warehouse (updated)",
        "database_url": "postgresql://postgres:postgres@main-db:5432/main_db",
        "is_default": False
    }}}
    display_name: str | None = Field(None, max_length=255)
    database_url: str | None = Field(None, min_length=8)
    is_default: bool | None = None


class DefaultSourceBody(BaseModel):
    model_config = {"json_schema_extra": {"example": {"key": "main-db"}}}
    key: str = Field(..., min_length=1, max_length=64)


@router.get(
    "/data-sources",
    response_model=DataSourcesListResponse,
    summary="Список источников (без DSN)",
    description="Публичные поля и ключ источника по умолчанию.",
)
async def list_data_sources():
    from app.services.data_sources_store import get_default_source_key

    items = [DataSourcePublic(**x) for x in list_sources_public()]
    return DataSourcesListResponse(items=items, default_key=get_default_source_key())


@router.get(
    "/data-sources/allowed-keys",
    response_model=AllowedDataSourceKeysResponse,
    summary="Ключи источников, доступных роли",
    description="Учитывает analytics_access_policies и X-User-Role (ADMIN — все источники).",
)
async def list_allowed_data_source_keys(
    x_user_role: Optional[str] = Header(
        None,
        alias="X-User-Role",
        description="Роль из BFF; по умолчанию USER",
    ),
):
    from app.services import access_policy_store as aps

    role = (x_user_role or "USER").strip()
    keys = aps.list_allowed_source_keys_for_role(role)
    return AllowedDataSourceKeysResponse(keys=keys)


@router.post(
    "/data-sources",
    response_model=DataSourcePublic,
    summary="Добавить источник",
    description="Если задан ANALYTICS_SOURCES_WRITE_TOKEN — заголовок обязателен и должен совпадать.",
)
async def add_data_source(
    body: DataSourceCreateBody,
    background_tasks: BackgroundTasks,
    x_analytics_sources_write_token: Optional[str] = Header(
        None,
        alias="X-Analytics-Sources-Write-Token",
        description="Токен записи источников (если включён в настройках)",
    ),
):
    _require_write_token(x_analytics_sources_write_token)
    try:
        row = create_source(
            body.key,
            body.display_name,
            body.database_url,
            body.set_as_default,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    dispose_analytics_engine_cache()
    schema_cache.invalidate()
    refresh_schema_cache()

    async def _enqueue_templates() -> None:
        try:
            await publish_template_plan_request(row["key"])
        except Exception:
            logger.exception(
                "enqueue report template plan failed for source_key=%s", row["key"]
            )

    background_tasks.add_task(_enqueue_templates)
    return DataSourcePublic(**row)


@router.patch(
    "/data-sources/{source_key}",
    response_model=DataSourcePublic,
    summary="Изменить источник",
)
async def patch_data_source(
    source_key: str,
    body: DataSourcePatchBody,
    x_analytics_sources_write_token: Optional[str] = Header(
        None,
        alias="X-Analytics-Sources-Write-Token",
        description="Токен записи источников (если включён)",
    ),
):
    _require_write_token(x_analytics_sources_write_token)
    try:
        sk = normalize_source_key(source_key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    try:
        row = update_source(
            sk,
            display_name=body.display_name,
            database_url=body.database_url,
            is_default=body.is_default,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="источник не найден")
    dispose_analytics_engine_cache()
    schema_cache.invalidate()
    refresh_schema_cache()
    return DataSourcePublic(**row)


@router.delete(
    "/data-sources/{source_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить источник",
)
async def remove_data_source(
    source_key: str,
    x_analytics_sources_write_token: Optional[str] = Header(
        None,
        alias="X-Analytics-Sources-Write-Token",
        description="Токен записи источников (если включён)",
    ),
):
    _require_write_token(x_analytics_sources_write_token)
    try:
        sk = normalize_source_key(source_key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    ok = delete_source(sk)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="источник не найден")
    dispose_analytics_engine_cache()
    schema_cache.invalidate()
    refresh_schema_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/data-sources/default",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Назначить источник по умолчанию",
)
async def put_default_data_source(
    body: DefaultSourceBody,
    x_analytics_sources_write_token: Optional[str] = Header(
        None,
        alias="X-Analytics-Sources-Write-Token",
        description="Токен записи источников (если включён)",
    ),
):
    _require_write_token(x_analytics_sources_write_token)
    try:
        sk = normalize_source_key(body.key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    ok = set_default_source(sk)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="источник не найден")
    dispose_analytics_engine_cache()
    schema_cache.invalidate()
    refresh_schema_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
