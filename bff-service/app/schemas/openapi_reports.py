# Синхронизировать с report-task-service/app/schemas/tasks.py (поля ответов API).
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ScheduleType = Literal["once", "daily", "weekly", "monthly", "yearly"]
RunStatus = Literal["pending", "running", "done", "failed"]


class TaskApi(BaseModel):
    id: str = Field(..., description="UUID задачи")
    title: str
    instruction: str
    user_id: str
    analytics_source_key: str
    schedule_type: ScheduleType
    timezone: str
    once_at: Optional[datetime] = None
    daily_time: Optional[str] = None
    weekly_day: Optional[int] = None
    weekly_time: Optional[str] = None
    monthly_day: Optional[int] = None
    monthly_time: Optional[str] = None
    yearly_date_ddmm: Optional[str] = None
    yearly_time: Optional[str] = None
    is_active: bool
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    runs_count: int
    created_at: datetime
    updated_at: datetime
    last_report_sentence: Optional[str] = Field(
        default=None,
        description="Первое предложение из последнего завершённого отчёта (status=done) по задаче; null, если таких отчётов нет.",
    )
    reports: list["ReportRunApi"] = Field(
        default_factory=list,
        description="Массив прогонов отчёта для этой задачи (используется в детальном ответе задачи).",
    )


class TaskListResponse(BaseModel):
    items: list[TaskApi]
    total: int


class ReportRunApi(BaseModel):
    id: str
    task_id: Optional[str] = None
    user_id: str
    status: RunStatus = Field(..., description="Статус прогона отчёта")
    query_text: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    result_summary: Optional[str] = None
    result_payload: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ReportRunListResponse(BaseModel):
    items: list[ReportRunApi]
    total: int


TaskApi.model_rebuild()
