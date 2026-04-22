from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


ScheduleType = Literal["once", "daily", "monthly", "yearly"]
RunStatus = Literal["pending", "running", "done", "failed"]


class TaskScheduleBody(BaseModel):
    schedule_type: ScheduleType
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    once_at: Optional[datetime] = None
    daily_time: Optional[str] = None
    monthly_day: Optional[int] = Field(default=None, ge=1, le=31)
    monthly_time: Optional[str] = None
    yearly_date_ddmm: Optional[str] = None
    yearly_time: Optional[str] = None

    @model_validator(mode="after")
    def validate_shape(self):
        st = self.schedule_type
        if st == "once" and not self.once_at:
            raise ValueError("once_at is required for once schedule")
        if st == "daily" and not self.daily_time:
            raise ValueError("daily_time is required for daily schedule")
        if st == "monthly" and (self.monthly_day is None or not self.monthly_time):
            raise ValueError("monthly_day and monthly_time are required for monthly schedule")
        if st == "yearly" and (not self.yearly_date_ddmm or not self.yearly_time):
            raise ValueError("yearly_date_ddmm and yearly_time are required for yearly schedule")
        return self


class TaskCreateBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Ежедневный отчет по заказам",
                "instruction": "Покажи динамику заказов и средний чек за сегодня.",
                "analytics_source_key": "main-db",
                "schedule": {"schedule_type": "daily", "daily_time": "09:00", "timezone": "Europe/Moscow"},
            }
        }
    )
    title: str = Field(..., min_length=1, max_length=500)
    instruction: str = Field(..., min_length=1)
    analytics_source_key: str = Field(..., min_length=1, max_length=64)
    schedule: TaskScheduleBody
    is_active: bool = True


class TaskPatchBody(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    instruction: Optional[str] = Field(default=None, min_length=1)
    analytics_source_key: Optional[str] = Field(default=None, min_length=1, max_length=64)
    schedule: Optional[TaskScheduleBody] = None
    is_active: Optional[bool] = None


class TaskApi(BaseModel):
    id: str
    title: str
    instruction: str
    user_id: str
    analytics_source_key: str
    schedule_type: ScheduleType
    timezone: str
    once_at: Optional[datetime] = None
    daily_time: Optional[str] = None
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


class TaskListResponse(BaseModel):
    items: list[TaskApi]
    total: int


class ReportRunApi(BaseModel):
    id: str
    task_id: str | None
    user_id: str
    status: RunStatus
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


class ReportCreateBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": None,
                "status": "pending",
                "query_text": "Построй срез заказов за последние 7 дней",
                "result_summary": None,
                "result_payload": None,
            }
        }
    )
    task_id: str | None = None
    status: RunStatus = "pending"
    query_text: str = Field(..., min_length=1)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    result_summary: Optional[str] = None
    result_payload: Optional[dict[str, Any]] = None


class ReportPatchBody(BaseModel):
    task_id: str | None = None
    status: Optional[RunStatus] = None
    query_text: Optional[str] = Field(default=None, min_length=1)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    result_summary: Optional[str] = None
    result_payload: Optional[dict[str, Any]] = None


class ReportResultBody(BaseModel):
    status: Literal["done"]
    result_summary: Optional[str] = None
    result_payload: Optional[dict[str, Any]] = None


class ReportErrorBody(BaseModel):
    status: Literal["failed"]
    error: str
