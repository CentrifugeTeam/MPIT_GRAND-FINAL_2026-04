from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.services.analytics_service import AnalyticsProxy

router = APIRouter()
_proxy = AnalyticsProxy()


class TaskScheduleBody(BaseModel):
    schedule_type: str
    timezone: str | None = "UTC"
    once_at: str | None = None
    daily_time: str | None = None
    monthly_day: int | None = None
    monthly_time: str | None = None
    yearly_date_ddmm: str | None = None
    yearly_time: str | None = None


class CreateReportTaskBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    instruction: str = Field(..., min_length=1)
    analytics_source_key: str = Field(..., min_length=1, max_length=64)
    is_active: bool = True
    schedule: TaskScheduleBody


class PatchReportTaskBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    instruction: str | None = Field(default=None, min_length=1)
    analytics_source_key: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None
    schedule: TaskScheduleBody | None = None


class CreateReportBody(BaseModel):
    task_id: str | None = None
    status: str = "pending"
    query_text: str = Field(..., min_length=1)
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result_summary: str | None = None
    result_payload: dict[str, Any] | None = None


class PatchReportBody(BaseModel):
    task_id: str | None = None
    status: str | None = None
    query_text: str | None = Field(default=None, min_length=1)
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result_summary: str | None = None
    result_payload: dict[str, Any] | None = None


@router.post("/tasks")
async def create_report_task(
    body: CreateReportTaskBody,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.create_report_task(uid, body.model_dump(exclude_none=True))


@router.get("/tasks")
async def list_report_tasks(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.list_report_tasks(uid, limit=limit, offset=offset)


@router.get("/tasks/{task_id}")
async def get_report_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_report_task(uid, task_id)


@router.patch("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_report_task(
    task_id: str,
    body: PatchReportTaskBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    uid = current_user.get("uuid")
    await _proxy.patch_report_task(uid, task_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_report_task(uid, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tasks/{task_id}/reports")
async def list_report_runs(
    task_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.list_report_runs(uid, task_id, limit=limit, offset=offset)


@router.get("/reports/{report_id}")
async def get_report_run(
    report_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.get_report_run(uid, report_id)


@router.get("/reports")
async def list_reports(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.list_report_runs_for_user(uid, limit=limit, offset=offset)


@router.post("/reports")
async def create_report(
    body: CreateReportBody,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    uid = current_user.get("uuid")
    return await _proxy.create_report_run(uid, body.model_dump(exclude_none=True))


@router.patch("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_report(
    report_id: str,
    body: PatchReportBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    uid = current_user.get("uuid")
    await _proxy.patch_report_run(uid, report_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    await _proxy.delete_report_run(uid, report_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
