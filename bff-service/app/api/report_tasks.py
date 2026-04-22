from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.auth import get_current_user
from app.services.analytics_service import AnalyticsProxy

router = APIRouter()
_proxy = AnalyticsProxy()


class TaskScheduleBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": (
                "Allowed schedule_type values: once, daily, weekly, monthly, yearly. "
                "Required fields: once->once_at, daily->daily_time, "
                "weekly->weekly_day + weekly_time, monthly->monthly_day + monthly_time, "
                "yearly->yearly_date_ddmm + yearly_time."
            ),
            "examples": [
                {"schedule_type": "daily", "timezone": "Europe/Moscow", "daily_time": "09:00"},
                {"schedule_type": "weekly", "timezone": "Europe/Moscow", "weekly_day": 1, "weekly_time": "09:00"},
            ],
        }
    )
    schedule_type: Literal["once", "daily", "weekly", "monthly", "yearly"] = Field(
        ...,
        description="one of: once, daily, weekly, monthly, yearly",
    )
    timezone: str | None = Field(default="UTC", description="IANA timezone, e.g. Europe/Moscow")
    once_at: str | None = Field(default=None, description="ISO datetime for once")
    daily_time: str | None = Field(default=None, description="HH:MM for daily")
    weekly_day: int | None = Field(default=None, ge=1, le=7, description="ISO weekday 1..7 for weekly")
    weekly_time: str | None = Field(default=None, description="HH:MM for weekly")
    monthly_day: int | None = Field(default=None, ge=1, le=31, description="Day 1..31 for monthly")
    monthly_time: str | None = Field(default=None, description="HH:MM for monthly")
    yearly_date_ddmm: str | None = Field(default=None, description="dd:mm for yearly")
    yearly_time: str | None = Field(default=None, description="HH:MM for yearly")


class CreateReportTaskBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Weekly churn report",
                "instruction": "Покажи отток пользователей за неделю",
                "analytics_source_key": "main-db",
                "is_active": True,
                "schedule": {
                    "schedule_type": "weekly",
                    "timezone": "Europe/Moscow",
                    "once_at": None,
                    "daily_time": None,
                    "weekly_day": 1,
                    "weekly_time": "09:00",
                    "monthly_day": None,
                    "monthly_time": None,
                    "yearly_date_ddmm": None,
                    "yearly_time": None,
                },
            }
        }
    )
    title: str = Field(..., min_length=1, max_length=500, description="Task title shown in UI.")
    instruction: str = Field(..., min_length=1, description="LLM instruction/query executed by schedule.")
    analytics_source_key: str = Field(..., min_length=1, max_length=64, description="Target data source key.")
    is_active: bool = Field(default=True, description="Enable or disable scheduled execution.")
    schedule: TaskScheduleBody = Field(..., description="Schedule configuration.")


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
