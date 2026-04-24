import uuid

from fastapi import APIRouter, Header, HTTPException, Query, Response, status

from app.core.config import get_settings
from app.schemas.templates import (
    TaskTemplateApi,
    TaskTemplateBulkBody,
    TaskTemplateBulkResponse,
    TaskTemplateCreateBody,
    TaskTemplateListResponse,
    TaskTemplatePatchBody,
)
from app.services.template_store import (
    bulk_insert_system_templates,
    create_template,
    delete_template,
    get_template,
    list_templates,
    patch_template,
)

router = APIRouter()


def _allowed_analytics_source_keys_from_header(
    raw: str | None,
) -> list[str] | None:
    """None — без фильтра; список (в т.ч. пустой) — только шаблоны с analytics_source_key из списка."""
    if raw is None:
        return None
    return [p.strip() for p in raw.split(",") if p.strip()]


@router.post(
    "/task-templates",
    response_model=TaskTemplateApi,
    summary="Создать шаблон отчётной задачи",
    description="Пресет title/instruction/analytics_source_key и расписание (once/daily/weekly/monthly/yearly).",
)
async def create_template_route(
    body: TaskTemplateCreateBody,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца (BFF)"),
):
    row = create_template(x_user_id, body.model_dump(exclude_none=True))
    return TaskTemplateApi.model_validate(row)


@router.get(
    "/task-templates",
    response_model=TaskTemplateListResponse,
    summary="Список шаблонов пользователя",
)
async def list_templates_route(
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
    x_allowed_analytics_source_keys: str | None = Header(
        None,
        alias="X-Allowed-Analytics-Source-Keys",
        description="Список ключей через запятую; если заголовок передан — фильтр по источнику",
    ),
):
    allowed = _allowed_analytics_source_keys_from_header(x_allowed_analytics_source_keys)
    items, total = list_templates(
        x_user_id,
        limit=limit,
        offset=offset,
        allowed_analytics_source_keys=allowed,
    )
    return TaskTemplateListResponse(
        items=[TaskTemplateApi.model_validate(i) for i in items],
        total=total,
    )


@router.get(
    "/task-templates/{template_id}",
    response_model=TaskTemplateApi,
    summary="Шаблон по id",
)
async def get_template_route(
    template_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
    x_allowed_analytics_source_keys: str | None = Header(
        None,
        alias="X-Allowed-Analytics-Source-Keys",
        description="Список ключей через запятую; если передан — шаблон вне списка = 404",
    ),
):
    allowed = _allowed_analytics_source_keys_from_header(x_allowed_analytics_source_keys)
    row = get_template(x_user_id, str(template_id), allowed_analytics_source_keys=allowed)
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    return TaskTemplateApi.model_validate(row)


@router.post(
    "/task-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Обновить шаблон",
    description="Частичное обновление: title, instruction, analytics_source_key, schedule.",
)
async def patch_template_route(
    template_id: uuid.UUID,
    body: TaskTemplatePatchBody,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    ok = patch_template(x_user_id, str(template_id), payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/task-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить шаблон",
)
async def delete_template_route(
    template_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    ok = delete_template(x_user_id, str(template_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/internal/report-templates/bulk",
    response_model=TaskTemplateBulkResponse,
    summary="Внутренний: массовая вставка системных шаблонов",
    description="Только с корректным X-Report-Internal-Token (analytics-service).",
    tags=["internal"],
)
async def bulk_system_templates_internal(
    body: TaskTemplateBulkBody,
    x_report_internal_token: str = Header(
        "",
        alias="X-Report-Internal-Token",
        description="Должен совпадать с REPORT_TASK_INTERNAL_TOKEN",
    ),
):
    if x_report_internal_token != get_settings().REPORT_TASK_INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    s = get_settings()
    n = bulk_insert_system_templates(
        s.REPORT_TEMPLATE_SYSTEM_USER_ID,
        [t.model_dump(mode="json", exclude_none=True) for t in body.templates],
    )
    return TaskTemplateBulkResponse(inserted=n)
