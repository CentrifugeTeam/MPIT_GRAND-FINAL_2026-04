from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.auth import get_current_user
from app.schemas.openapi_reports import (
    ReportRunApi,
    ReportRunListResponse,
    TaskApi,
    TaskListResponse,
    TaskTemplateApi,
    TaskTemplateListResponse,
)
from app.services.analytics_service import AnalyticsProxy

router = APIRouter()
_proxy = AnalyticsProxy()

_AUTH = "JWT Bearer; X-User-Id / X-User-Role проксируются в report-task-service."


async def _require_analytics_source_in_policy(
    uid: str, role: str, analytics_source_key: str
) -> None:
    allowed = await _proxy.list_allowed_analytics_source_keys(uid, user_role=role)
    sk = (analytics_source_key or "").strip()
    if sk not in set(allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к выбранному источнику данных",
        )


class TaskScheduleBody(BaseModel):
    """Совпадает с report-task-service/app/schemas/tasks.py:TaskScheduleBody (валидация полей по schedule_type)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"schedule_type": "daily", "timezone": "Europe/Moscow", "daily_time": "09:00"},
                {
                    "schedule_type": "weekly",
                    "timezone": "Europe/Moscow",
                    "weekly_day": 1,
                    "weekly_time": "09:00",
                },
            ],
        },
    )
    schedule_type: Literal["once", "daily", "weekly", "monthly", "yearly"] = Field(
        ...,
        description="Режим: once | daily | weekly | monthly | yearly",
    )
    timezone: str = Field(
        default="UTC",
        min_length=1,
        max_length=64,
        description="IANA-часовой пояс, например Europe/Moscow",
    )
    once_at: Optional[datetime] = Field(default=None, description="Только для once — ISO datetime.")
    daily_time: Optional[str] = Field(default=None, description="Только для daily — HH:MM.")
    weekly_day: Optional[int] = Field(
        default=None,
        ge=1,
        le=7,
        description="Только для weekly — день недели ISO 1=пн … 7=вс.",
    )
    weekly_time: Optional[str] = Field(default=None, description="Только для weekly — HH:MM.")
    monthly_day: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        description="Только для monthly — число месяца 1..31.",
    )
    monthly_time: Optional[str] = Field(default=None, description="Только для monthly — HH:MM.")
    yearly_date_ddmm: Optional[str] = Field(
        default=None,
        description="Только для yearly — формат dd:mm.",
    )
    yearly_time: Optional[str] = Field(default=None, description="Только для yearly — HH:MM.")

    @model_validator(mode="after")
    def validate_shape(self):
        st = self.schedule_type
        if st == "once":
            if not self.once_at:
                raise ValueError("once_at is required for once schedule")
            if any(
                v is not None
                for v in (
                    self.daily_time,
                    self.weekly_day,
                    self.weekly_time,
                    self.monthly_day,
                    self.monthly_time,
                    self.yearly_date_ddmm,
                    self.yearly_time,
                )
            ):
                raise ValueError("only once_at may be set for once schedule")
        if st == "daily":
            if not self.daily_time:
                raise ValueError("daily_time is required for daily schedule")
            if any(
                v is not None
                for v in (
                    self.once_at,
                    self.weekly_day,
                    self.weekly_time,
                    self.monthly_day,
                    self.monthly_time,
                    self.yearly_date_ddmm,
                    self.yearly_time,
                )
            ):
                raise ValueError("only daily_time may be set for daily schedule")
        if st == "weekly":
            if self.weekly_day is None or not self.weekly_time:
                raise ValueError("weekly_day and weekly_time are required for weekly schedule")
            if any(
                v is not None
                for v in (
                    self.once_at,
                    self.daily_time,
                    self.monthly_day,
                    self.monthly_time,
                    self.yearly_date_ddmm,
                    self.yearly_time,
                )
            ):
                raise ValueError("only weekly_day/weekly_time may be set for weekly schedule")
        if st == "monthly":
            if self.monthly_day is None or not self.monthly_time:
                raise ValueError("monthly_day and monthly_time are required for monthly schedule")
            if any(
                v is not None
                for v in (
                    self.once_at,
                    self.daily_time,
                    self.weekly_day,
                    self.weekly_time,
                    self.yearly_date_ddmm,
                    self.yearly_time,
                )
            ):
                raise ValueError("only monthly_day/monthly_time may be set for monthly schedule")
        if st == "yearly":
            if not self.yearly_date_ddmm or not self.yearly_time:
                raise ValueError("yearly_date_ddmm and yearly_time are required for yearly schedule")
            if any(
                v is not None
                for v in (
                    self.once_at,
                    self.daily_time,
                    self.weekly_day,
                    self.weekly_time,
                    self.monthly_day,
                    self.monthly_time,
                )
            ):
                raise ValueError("only yearly_date_ddmm/yearly_time may be set for yearly schedule")
        return self


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
            },
        },
    )
    title: str = Field(..., min_length=1, max_length=500, description="Заголовок задачи в UI")
    instruction: str = Field(
        ...,
        min_length=1,
        description="Текст запроса/инструкция для LLM при срабатывании расписания",
    )
    analytics_source_key: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Ключ источника данных (main-db и т.д.)",
    )
    is_active: bool = Field(default=True, description="Включено ли расписание")
    schedule: TaskScheduleBody = Field(..., description="Расписание запусков")


class PatchReportTaskBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Обновлённый заголовок",
                "is_active": False,
            },
        },
    )
    title: str | None = Field(default=None, min_length=1, max_length=500)
    instruction: str | None = Field(default=None, min_length=1)
    analytics_source_key: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None
    schedule: TaskScheduleBody | None = None


class CreateTaskTemplateBody(BaseModel):
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
            },
        },
    )
    title: str = Field(..., min_length=1, max_length=500)
    instruction: str = Field(..., min_length=1)
    analytics_source_key: str = Field(..., min_length=1, max_length=64)
    schedule: TaskScheduleBody = Field(..., description="Расписание шаблона (once/daily/weekly/monthly/yearly)")


class PatchTaskTemplateBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    instruction: str | None = Field(default=None, min_length=1)
    analytics_source_key: str | None = Field(default=None, min_length=1, max_length=64)
    schedule: TaskScheduleBody | None = None


class CreateReportBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": None,
                "status": "pending",
                "query_text": "Построй срез заказов за последние 7 дней",
                "started_at": None,
                "finished_at": None,
                "error": None,
                "result_summary": None,
                "result_payload": None,
            },
        },
    )
    task_id: str | None = Field(default=None, description="Привязка к задаче (опционально)")
    status: str = Field(default="pending", description="Начальный статус прогона")
    query_text: str = Field(..., min_length=1, description="Текст запроса для отчёта")
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result_summary: str | None = None
    result_payload: dict[str, Any] | None = None


class PatchReportBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "done", "result_summary": "Готово"},
        },
    )
    task_id: str | None = None
    status: str | None = None
    query_text: str | None = Field(default=None, min_length=1)
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result_summary: str | None = None
    result_payload: dict[str, Any] | None = None


@router.post(
    "/tasks",
    response_model=TaskApi,
    summary="Создать отчётную задачу по расписанию",
    description="Прокси в report-task-service. " + _AUTH,
)
async def create_report_task(
    body: CreateReportTaskBody,
    current_user: dict = Depends(get_current_user),
) -> TaskApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.create_report_task(
        uid, body.model_dump(mode="json", exclude_none=True), user_role=role
    )
    return TaskApi.model_validate(raw)


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="Список отчётных задач пользователя",
    description=_AUTH,
)
async def list_report_tasks(
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user: dict = Depends(get_current_user),
) -> TaskListResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.list_report_tasks(uid, limit=limit, offset=offset, user_role=role)
    return TaskListResponse.model_validate(raw)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskApi,
    summary="Получить задачу по id",
    description=_AUTH,
    responses={404: {"description": "Задача не найдена"}},
)
async def get_report_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
) -> TaskApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.get_report_task(uid, task_id, user_role=role)
    return TaskApi.model_validate(raw)


@router.post(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Обновить задачу",
    description="Прокси в report-task-service. Обновляет любые переданные поля задачи (тип/время расписания, инструкция, источник данных и т.д.). " + _AUTH,
)
async def replace_report_task(
    task_id: str,
    body: PatchReportTaskBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    payload = body.model_dump(mode="json", exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.replace_report_task(uid, task_id, payload, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
    description=_AUTH,
)
async def delete_report_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_report_task(uid, task_id, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/templates",
    response_model=TaskTemplateApi,
    summary="Создать шаблон отчётной задачи",
    description="Прокси в report-task-service. " + _AUTH,
)
async def create_report_task_template(
    body: CreateTaskTemplateBody,
    current_user: dict = Depends(get_current_user),
) -> TaskTemplateApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _require_analytics_source_in_policy(uid, role, body.analytics_source_key)
    raw = await _proxy.create_report_task_template(
        uid, body.model_dump(mode="json", exclude_none=True), user_role=role
    )
    return TaskTemplateApi.model_validate(raw)


@router.get(
    "/templates",
    response_model=TaskTemplateListResponse,
    summary="Список шаблонов отчётных задач",
    description="Прокси в report-task-service. " + _AUTH,
)
async def list_report_task_templates(
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user: dict = Depends(get_current_user),
) -> TaskTemplateListResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.list_report_task_templates(
        uid, limit=limit, offset=offset, user_role=role
    )
    return TaskTemplateListResponse.model_validate(raw)


@router.get(
    "/templates/{template_id}",
    response_model=TaskTemplateApi,
    summary="Получить шаблон по id",
    description="Прокси в report-task-service. " + _AUTH,
    responses={404: {"description": "Шаблон не найден"}},
)
async def get_report_task_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
) -> TaskTemplateApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.get_report_task_template(uid, template_id, user_role=role)
    return TaskTemplateApi.model_validate(raw)


@router.post(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Обновить шаблон отчётной задачи",
    description="Прокси в report-task-service (частичное обновление). " + _AUTH,
)
async def replace_report_task_template(
    template_id: str,
    body: PatchTaskTemplateBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    payload = body.model_dump(mode="json", exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    sk = payload.get("analytics_source_key")
    if isinstance(sk, str) and sk.strip():
        await _require_analytics_source_in_policy(uid, role, sk)
    await _proxy.replace_report_task_template(uid, template_id, payload, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить шаблон отчётной задачи",
    description="Прокси в report-task-service. " + _AUTH,
)
async def delete_report_task_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_report_task_template(uid, template_id, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/dispatch",
    response_model=ReportRunApi,
    summary="Запустить задачу вручную через очередь",
    description="Прокси в report-task-service. Создаёт прогон и отправляет его в очередь выполнения. " + _AUTH,
)
async def dispatch_report_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
) -> ReportRunApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.dispatch_report_task(uid, task_id, user_role=role)
    return ReportRunApi.model_validate(raw)


@router.get(
    "/tasks/{task_id}/reports",
    response_model=ReportRunListResponse,
    summary="Прогоны отчётов по задаче",
    description=_AUTH,
)
async def list_report_runs(
    task_id: str,
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user: dict = Depends(get_current_user),
) -> ReportRunListResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.list_report_runs(uid, task_id, limit=limit, offset=offset, user_role=role)
    return ReportRunListResponse.model_validate(raw)


@router.get(
    "/history",
    response_model=ReportRunListResponse,
    summary="История прогонов отчётов пользователя",
    description="Прокси в report-task-service: все прогоны пользователя. " + _AUTH,
)
async def list_report_history(
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
    current_user: dict = Depends(get_current_user),
) -> ReportRunListResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.list_report_runs_for_user(uid, limit=limit, offset=offset, user_role=role)
    return ReportRunListResponse.model_validate(raw)


@router.get(
    "/reports/{report_id}",
    response_model=ReportRunApi,
    summary="Получить один прогон отчёта",
    description=_AUTH,
)
async def get_report_run(
    report_id: str,
    current_user: dict = Depends(get_current_user),
) -> ReportRunApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.get_report_run(uid, report_id, user_role=role)
    return ReportRunApi.model_validate(raw)


@router.post(
    "/reports",
    response_model=ReportRunApi,
    summary="Создать прогон отчёта (ручной)",
    description=_AUTH,
)
async def create_report(
    body: CreateReportBody,
    current_user: dict = Depends(get_current_user),
) -> ReportRunApi:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.create_report_run(
        uid, body.model_dump(mode="json", exclude_none=True), user_role=role
    )
    return ReportRunApi.model_validate(raw)


@router.patch(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Обновить прогон отчёта",
    description=_AUTH,
)
async def patch_report(
    report_id: str,
    body: PatchReportBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    payload = body.model_dump(mode="json", exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.patch_report_run(uid, report_id, payload, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить прогон отчёта",
    description=_AUTH,
)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_report_run(uid, report_id, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
