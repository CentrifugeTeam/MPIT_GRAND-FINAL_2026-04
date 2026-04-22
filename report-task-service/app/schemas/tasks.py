from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


ScheduleType = Literal["once", "daily", "weekly", "monthly", "yearly"]
RunStatus = Literal["pending", "running", "done", "failed"]


class TaskScheduleBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": (
                "schedule_type controls required fields: "
                "once -> once_at(ISO datetime), "
                "daily -> daily_time(HH:MM), "
                "weekly -> weekly_day(1..7) + weekly_time(HH:MM), "
                "monthly -> monthly_day(1..31) + monthly_time(HH:MM), "
                "yearly -> yearly_date_ddmm(dd:mm) + yearly_time(HH:MM)."
            ),
            "examples": [
                {"schedule_type": "once", "timezone": "Europe/Moscow", "once_at": "2026-05-01T09:00:00+03:00"},
                {"schedule_type": "daily", "timezone": "Europe/Moscow", "daily_time": "09:00"},
                {"schedule_type": "weekly", "timezone": "Europe/Moscow", "weekly_day": 1, "weekly_time": "09:00"},
                {"schedule_type": "monthly", "timezone": "Europe/Moscow", "monthly_day": 1, "monthly_time": "10:30"},
                {"schedule_type": "yearly", "timezone": "Europe/Moscow", "yearly_date_ddmm": "15:01", "yearly_time": "11:00"},
            ],
        }
    )
    schedule_type: ScheduleType = Field(
        ...,
        description="Schedule mode: once, daily, weekly, monthly, yearly.",
    )
    timezone: str = Field(default="UTC", min_length=1, max_length=64, description="IANA timezone, e.g. Europe/Moscow, UTC.")
    once_at: Optional[datetime] = Field(default=None, description="Used only for schedule_type=once. ISO datetime.")
    daily_time: Optional[str] = Field(default=None, description="Used only for schedule_type=daily. Format HH:MM.")
    weekly_day: Optional[int] = Field(default=None, ge=1, le=7, description="Used only for schedule_type=weekly. ISO weekday where 1=Monday ... 7=Sunday.")
    weekly_time: Optional[str] = Field(default=None, description="Used only for schedule_type=weekly. Format HH:MM.")
    monthly_day: Optional[int] = Field(default=None, ge=1, le=31, description="Used only for schedule_type=monthly. Day of month.")
    monthly_time: Optional[str] = Field(default=None, description="Used only for schedule_type=monthly. Format HH:MM.")
    yearly_date_ddmm: Optional[str] = Field(default=None, description="Used only for schedule_type=yearly. Format dd:mm.")
    yearly_time: Optional[str] = Field(default=None, description="Used only for schedule_type=yearly. Format HH:MM.")

    @model_validator(mode="after")
    def validate_shape(self):
        st = self.schedule_type
        if st == "once":
            if not self.once_at:
                raise ValueError("once_at is required for once schedule")
            if any(v is not None for v in (self.daily_time, self.weekly_day, self.weekly_time, self.monthly_day, self.monthly_time, self.yearly_date_ddmm, self.yearly_time)):
                raise ValueError("only once_at may be set for once schedule")
        if st == "daily":
            if not self.daily_time:
                raise ValueError("daily_time is required for daily schedule")
            if any(v is not None for v in (self.once_at, self.weekly_day, self.weekly_time, self.monthly_day, self.monthly_time, self.yearly_date_ddmm, self.yearly_time)):
                raise ValueError("only daily_time may be set for daily schedule")
        if st == "weekly":
            if self.weekly_day is None or not self.weekly_time:
                raise ValueError("weekly_day and weekly_time are required for weekly schedule")
            if any(v is not None for v in (self.once_at, self.daily_time, self.monthly_day, self.monthly_time, self.yearly_date_ddmm, self.yearly_time)):
                raise ValueError("only weekly_day/weekly_time may be set for weekly schedule")
        if st == "monthly":
            if self.monthly_day is None or not self.monthly_time:
                raise ValueError("monthly_day and monthly_time are required for monthly schedule")
            if any(v is not None for v in (self.once_at, self.daily_time, self.weekly_day, self.weekly_time, self.yearly_date_ddmm, self.yearly_time)):
                raise ValueError("only monthly_day/monthly_time may be set for monthly schedule")
        if st == "yearly":
            if not self.yearly_date_ddmm or not self.yearly_time:
                raise ValueError("yearly_date_ddmm and yearly_time are required for yearly schedule")
            if any(v is not None for v in (self.once_at, self.daily_time, self.weekly_day, self.weekly_time, self.monthly_day, self.monthly_time)):
                raise ValueError("only yearly_date_ddmm/yearly_time may be set for yearly schedule")
        return self


class TaskCreateBody(BaseModel):
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
    title: str = Field(..., min_length=1, max_length=500, description="Human readable task title shown in task list.")
    instruction: str = Field(..., min_length=1, description="Prompt/query text sent to LLM on each scheduled run.")
    analytics_source_key: str = Field(..., min_length=1, max_length=64, description="Data source key where SQL/analytics query must be executed (e.g. main-db).")
    schedule: TaskScheduleBody = Field(..., description="Schedule configuration that defines when report runs are created.")
    is_active: bool = Field(default=True, description="Whether scheduler should execute this task.")


class TaskPatchBody(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Patch task title.")
    instruction: Optional[str] = Field(default=None, min_length=1, description="Patch LLM instruction/query.")
    analytics_source_key: Optional[str] = Field(default=None, min_length=1, max_length=64, description="Patch data source key.")
    schedule: Optional[TaskScheduleBody] = Field(default=None, description="Patch full schedule object.")
    is_active: Optional[bool] = Field(default=None, description="Enable/disable scheduler execution for this task.")


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


class TaskListResponse(BaseModel):
    items: list[TaskApi]
    total: int


class ReportRunApi(BaseModel):
    id: str
    task_id: str | None
    user_id: str
    status: RunStatus = Field(..., description="Report run lifecycle status.")
    query_text: str = Field(..., description="Instruction snapshot used for this specific run.")
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
    task_id: str | None = Field(default=None, description="Optional link to task. Can be null for manual ad-hoc report.")
    status: RunStatus = Field(default="pending", description="Initial run status.")
    query_text: str = Field(..., min_length=1, description="Instruction/query text for this report run.")
    started_at: Optional[datetime] = Field(default=None, description="Run start timestamp (optional override).")
    finished_at: Optional[datetime] = Field(default=None, description="Run completion timestamp.")
    error: Optional[str] = Field(default=None, description="Error message if run failed.")
    result_summary: Optional[str] = Field(default=None, description="Human-readable report summary.")
    result_payload: Optional[dict[str, Any]] = Field(default=None, description="Structured report payload (tables/charts/meta).")


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
