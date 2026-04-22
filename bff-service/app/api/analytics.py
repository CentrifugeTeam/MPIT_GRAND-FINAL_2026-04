from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.services.analytics_service import AnalyticsProxy
from app.api.auth import get_current_user

router = APIRouter()
_proxy = AnalyticsProxy()


class QueryQualityBody(BaseModel):
    question: str = Field(..., min_length=1)
    sql: str | None = None
    interpretation_warnings: list[str] | None = None


class InterpretQuestionBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Покажи выручку по месяцам за 2025",
                "max_rows": 1000,
                "analytics_source_key": "main-db",
            }
        }
    )
    question: str = Field(..., min_length=1)
    max_rows: int | None = Field(default=None, ge=1)
    analytics_source_key: str | None = None


class PatchChatTitleBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"title": "Еженедельный отчет"}})
    title: str = Field(..., min_length=1, max_length=500)


class DataSourceCreateBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "main-db",
                "display_name": "Warehouse (main_db)",
                "database_url": "postgresql://postgres:postgres@main-db:5432/main_db",
                "set_as_default": True,
            }
        }
    )
    key: str
    display_name: str
    database_url: str
    set_as_default: bool = False


class DataSourcePatchBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "Warehouse (updated)",
                "database_url": "postgresql://postgres:postgres@main-db:5432/main_db",
                "is_default": False,
            }
        }
    )
    display_name: str | None = None
    database_url: str | None = None
    is_default: bool | None = None


class DefaultSourceBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"key": "main-db"}})
    key: str


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только роль ADMIN может менять источники данных",
        )


@router.post("/interpret-question")
async def interpret_question(
    body: InterpretQuestionBody,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Разбор вопроса и глоссарий для NL-чата (без sql_job)."""
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    return await _proxy.interpret_question(
        body.model_dump(exclude_none=True),
        user_id=uid,
        user_role=role,
    )


@router.post("/query-quality")
async def query_quality(
    body: QueryQualityBody,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    return await _proxy.query_quality(
        body.model_dump(exclude_none=True),
        user_id=uid,
        user_role=role,
    )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_history(
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_all_history(uid, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/history")
async def get_job_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    return await _proxy.get_history(uid, limit=limit, offset=offset, user_role=role)


@router.post("/chats")
async def create_nl_chat(
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    return await _proxy.create_nl_chat(uid, user_role=role)


@router.get("/chats/{conversation_id}/messages")
async def get_nl_chat_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    return await _proxy.get_nl_chat_messages(uid, conversation_id, user_role=role)


@router.patch("/chats/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_nl_chat_title(
    conversation_id: str,
    body: PatchChatTitleBody = Body(...),
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title required")
    role = str(current_user.get("role") or "USER")
    await _proxy.patch_nl_chat_title(uid, conversation_id, title, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/chats/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nl_chat(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_nl_chat(uid, conversation_id, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_job(job_id, uid, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/data-sources")
async def list_data_sources(
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    return await _proxy.list_data_sources()


@router.post("/data-sources")
async def create_data_source(
    body: DataSourceCreateBody,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return await _proxy.create_data_source(body.model_dump(exclude_none=True))


@router.patch("/data-sources/{source_key}")
async def patch_data_source(
    source_key: str,
    body: DataSourcePatchBody,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return await _proxy.patch_data_source(source_key, body.model_dump(exclude_none=True))


@router.delete("/data-sources/{source_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    source_key: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    await _proxy.delete_data_source(source_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/data-sources/default", status_code=status.HTTP_204_NO_CONTENT)
async def put_default_data_source(
    body: DefaultSourceBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    await _proxy.put_default_data_source(body.model_dump(exclude_none=True))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


