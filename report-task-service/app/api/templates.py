import uuid

from fastapi import APIRouter, Header, HTTPException, Query, Response, status

from app.schemas.templates import (
    TaskTemplateApi,
    TaskTemplateCreateBody,
    TaskTemplateListResponse,
    TaskTemplatePatchBody,
)
from app.services.template_store import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    patch_template,
)

router = APIRouter()


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
):
    items, total = list_templates(x_user_id, limit=limit, offset=offset)
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
):
    row = get_template(x_user_id, str(template_id))
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
