from typing import Any

from fastapi import APIRouter, Depends, Query

from app.services.analytics_service import AnalyticsProxy
from app.api.auth import get_current_user

router = APIRouter()
_proxy = AnalyticsProxy()


@router.get("/schema")
async def get_schema(
    refresh: bool = Query(False, description="Обновить кэш схемы"),
) -> dict[str, Any]:
    return await _proxy.get_schema(refresh)


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


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_job(job_id, uid)
