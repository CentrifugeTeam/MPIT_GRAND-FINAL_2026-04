from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status

from app.services.analytics_service import AnalyticsProxy
from app.api.auth import get_current_user

router = APIRouter()
_proxy = AnalyticsProxy()


@router.get("/schema")
async def get_schema(
    refresh: bool = Query(False, description="Обновить кэш схемы"),
) -> dict[str, Any]:
    return await _proxy.get_schema(refresh)


@router.get("/glossary")
async def get_glossary(
    q: str | None = Query(None, description="Поиск по глоссарию метрик"),
    limit: int = Query(500, ge=1, le=2000),
) -> dict[str, Any]:
    """Семантический слой (бизнес-термины) — прокси на analytics-service."""
    return await _proxy.get_glossary(q, limit)


@router.post("/generate-sql")
async def generate_sql(body: dict[str, Any]) -> dict[str, Any]:
    return await _proxy.generate_sql(body)


@router.post("/execute")
async def execute_sql(body: dict[str, Any]) -> dict[str, Any]:
    return await _proxy.execute(body)


@router.post("/ask")
async def ask(body: dict[str, Any]) -> dict[str, Any]:
    return await _proxy.ask(body)


@router.post("/ask-async")
async def ask_async(
    body: dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Асинхронный пайплайн: RabbitMQ → sql-generator-worker → WS `nl_sql_result`."""
    uid = current_user.get("uuid")
    return await _proxy.ask_async(body, uid)


@router.post("/jobs/{job_id}/rerun")
async def rerun_job(
    job_id: str,
    body: dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.rerun_job(job_id, body, uid)


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_job(job_id, uid)


@router.get("/history")
async def get_job_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_history(uid, limit=limit, offset=offset)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_history(
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_all_history(uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_job(job_id, uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
