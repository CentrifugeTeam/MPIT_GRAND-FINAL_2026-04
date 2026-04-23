from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.tasks import ScheduleType, TaskScheduleBody


class TaskTemplateCreateBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Еженедельный отчёт",
                "instruction": "Сводка за последние 7 дней",
                "analytics_source_key": "main-db",
                "schedule": {
                    "schedule_type": "weekly",
                    "timezone": "Europe/Moscow",
                    "weekly_day": 1,
                    "weekly_time": "09:00",
                },
            }
        }
    )
    title: str = Field(..., min_length=1, max_length=500)
    instruction: str = Field(..., min_length=1)
    analytics_source_key: str = Field(..., min_length=1, max_length=64)
    schedule: TaskScheduleBody


class TaskTemplatePatchBody(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    instruction: Optional[str] = Field(default=None, min_length=1)
    analytics_source_key: Optional[str] = Field(default=None, min_length=1, max_length=64)
    schedule: Optional[TaskScheduleBody] = None


class TaskTemplateApi(BaseModel):
    id: str
    user_id: str
    title: str
    instruction: str
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
    created_at: datetime
    updated_at: datetime


class TaskTemplateListResponse(BaseModel):
    items: list[TaskTemplateApi]
    total: int
