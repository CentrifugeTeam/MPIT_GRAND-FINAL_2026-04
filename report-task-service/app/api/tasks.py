import uuid

from fastapi import APIRouter, Header, HTTPException, Query, Response, status

from app.core.config import get_settings
from app.schemas.tasks import (
    ReportCreateBody,
    ReportErrorBody,
    ReportPatchBody,
    ReportResultBody,
    ReportRunApi,
    ReportRunListResponse,
    TaskApi,
    TaskCreateBody,
    TaskListResponse,
    TaskPatchBody,
)
from app.services.run_store import (
    create_manual_run,
    delete_run,
    get_run,
    list_runs,
    list_runs_for_user,
    mark_run_done,
    mark_run_failed,
    patch_run,
)
from app.services.task_store import create_task, delete_task, get_task, list_tasks, patch_task

router = APIRouter()


@router.post("/tasks", response_model=TaskApi)
async def create_task_route(
    body: TaskCreateBody,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    row = create_task(x_user_id, body.model_dump(exclude_none=True))
    return TaskApi.model_validate(row)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks_route(
    x_user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = list_tasks(x_user_id, limit=limit, offset=offset)
    return TaskListResponse(
        items=[TaskApi.model_validate(i) for i in items],
        total=total,
    )


@router.get("/tasks/{task_id}", response_model=TaskApi)
async def get_task_route(
    task_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    row = get_task(x_user_id, str(task_id))
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskApi.model_validate(row)


@router.patch("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_task_route(
    task_id: uuid.UUID,
    body: TaskPatchBody,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    ok = patch_task(x_user_id, str(task_id), payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_route(
    task_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    ok = delete_task(x_user_id, str(task_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tasks/{task_id}/reports", response_model=ReportRunListResponse)
async def list_task_reports_route(
    task_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if not get_task(x_user_id, str(task_id)):
        raise HTTPException(status_code=404, detail="Task not found")
    items, total = list_runs(str(task_id), limit=limit, offset=offset)
    return ReportRunListResponse(
        items=[ReportRunApi.model_validate(i) for i in items],
        total=total,
    )


@router.get("/reports/{report_id}", response_model=ReportRunApi)
async def get_report_route(
    report_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    row = get_run(str(report_id))
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    if row["user_id"] != x_user_id:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportRunApi.model_validate(row)


@router.get("/reports", response_model=ReportRunListResponse)
async def list_reports_route(
    x_user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items, total = list_runs_for_user(x_user_id, limit=limit, offset=offset)
    return ReportRunListResponse(
        items=[ReportRunApi.model_validate(i) for i in items],
        total=total,
    )


@router.post("/reports", response_model=ReportRunApi)
async def create_report_route(
    body: ReportCreateBody,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    payload = body.model_dump(exclude_none=True)
    task_id = payload.get("task_id")
    if task_id and not get_task(x_user_id, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    row = create_manual_run(x_user_id, payload)
    return ReportRunApi.model_validate(row)


@router.patch("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_report_route(
    report_id: uuid.UUID,
    body: ReportPatchBody,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update")
    task_id = payload.get("task_id")
    if task_id and not get_task(x_user_id, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    ok = patch_run(x_user_id, str(report_id), payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_route(
    report_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    ok = delete_run(x_user_id, str(report_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/internal/reports/{report_id}/result", status_code=status.HTTP_204_NO_CONTENT)
async def report_result_internal(
    report_id: uuid.UUID,
    body: ReportResultBody,
    x_report_internal_token: str = Header("", alias="X-Report-Internal-Token"),
):
    if x_report_internal_token != get_settings().REPORT_TASK_INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    ok = mark_run_done(str(report_id), body.result_summary, body.result_payload)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/internal/reports/{report_id}/error", status_code=status.HTTP_204_NO_CONTENT)
async def report_error_internal(
    report_id: uuid.UUID,
    body: ReportErrorBody,
    x_report_internal_token: str = Header("", alias="X-Report-Internal-Token"),
):
    if x_report_internal_token != get_settings().REPORT_TASK_INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    ok = mark_run_failed(str(report_id), body.error)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
