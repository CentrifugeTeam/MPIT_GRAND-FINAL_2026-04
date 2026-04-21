from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status

from app.services.analytics_service import AnalyticsProxy
from app.api.auth import get_current_user

router = APIRouter()
_proxy = AnalyticsProxy()


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только роль ADMIN может менять источники данных",
        )


@router.post("/interpret-question")
async def interpret_question(
    body: dict[str, Any],
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Разбор вопроса и глоссарий для NL-чата (без sql_job)."""
    return await _proxy.interpret_question(body)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_history(
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_all_history(uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/history")
async def get_job_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_history(uid, limit=limit, offset=offset)


@router.post("/chats")
async def create_nl_chat(
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.create_nl_chat(uid)


@router.get("/chats/{conversation_id}/messages")
async def get_nl_chat_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_nl_chat_messages(uid, conversation_id)


@router.patch("/chats/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_nl_chat_title(
    conversation_id: str,
    body: dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    title = str(body.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title required")
    await _proxy.patch_nl_chat_title(uid, conversation_id, title)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/chats/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nl_chat(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_nl_chat(uid, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_job(job_id, uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/data-sources")
async def list_data_sources(
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    return await _proxy.list_data_sources()


@router.post("/data-sources")
async def create_data_source(
    body: dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return await _proxy.create_data_source(body)


@router.patch("/data-sources/{source_key}")
async def patch_data_source(
    source_key: str,
    body: dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    _require_admin(current_user)
    return await _proxy.patch_data_source(source_key, body)


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
    body: dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    await _proxy.put_default_data_source(body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
