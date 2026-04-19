import uuid

from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.schemas.analytics import (
    AskAsyncResponse,
    AskResponse,
    ExecuteSqlRequest,
    ExecuteSqlResponse,
    GenerateSqlResponse,
    JobStatusResponse,
    QuestionRequest,
    SchemaResponse,
)
from app.services.chart_builder import build_chart
from app.services.db_schema import introspect_public
from app.services.llm_service import generate_sql
from app.services.query_executor import execute_select
from app.services import schema_cache
from app.services.sql_guard import allowed_table_set, validate_and_prepare_sql
from app.services.template_parser import resolve_template
from app.services.job_store import create_job, get_job
from app.services.rabbitmq_publish import rabbit_publish

router = APIRouter()

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.ANALYTICS_DATABASE_URL,
            pool_pre_ping=True,
        )
    return _engine


@router.get("/schema", response_model=SchemaResponse)
async def get_schema(
    refresh: bool = Query(False, description="Обновить кэш схемы из БД"),
):
    settings = get_settings()
    cached = schema_cache.get_cached(settings.SCHEMA_CACHE_TTL_SECONDS)
    if cached is not None and not refresh:
        return SchemaResponse(tables=cached, cached=True)

    engine = get_engine()
    try:
        tables = introspect_public(engine)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Не удалось прочитать схему БД: {e}",
        ) from e

    schema_cache.set_cached(tables)
    return SchemaResponse(tables=tables, cached=False)


@router.post("/generate-sql", response_model=GenerateSqlResponse)
async def generate_sql_route(body: QuestionRequest):
    settings = get_settings()
    cached = schema_cache.get_cached(settings.SCHEMA_CACHE_TTL_SECONDS)
    tables = cached
    if tables is None:
        engine = get_engine()
        try:
            tables = introspect_public(engine)
            schema_cache.set_cached(tables)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Не удалось прочитать схему БД: {e}",
            ) from e

    try:
        sql, explanation, excerpt = await generate_sql(body.question, tables)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка LLM: {e}",
        ) from e

    return GenerateSqlResponse(
        sql=sql.strip(),
        explanation=explanation,
        raw_llm_excerpt=excerpt,
    )


@router.post("/execute", response_model=ExecuteSqlResponse)
async def execute_sql_route(body: ExecuteSqlRequest):
    settings = get_settings()
    allowed = allowed_table_set()
    try:
        sql, warnings = validate_and_prepare_sql(
            body.sql,
            settings.QUERY_MAX_ROWS,
            allowed,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    engine = get_engine()

    try:
        cols, rows = execute_select(
            engine, sql, timeout_ms=settings.QUERY_TIMEOUT_MS
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка выполнения SQL: {e}",
        ) from e

    return ExecuteSqlResponse(
        sql=sql,
        columns=cols,
        rows=rows,
        row_count=len(rows),
        guard_warnings=warnings,
    )


@router.post("/ask", response_model=AskResponse)
async def ask_route(body: QuestionRequest):
    settings = get_settings()
    cached = schema_cache.get_cached(settings.SCHEMA_CACHE_TTL_SECONDS)
    tables = cached
    if tables is None:
        engine = get_engine()
        try:
            tables = introspect_public(engine)
            schema_cache.set_cached(tables)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Не удалось прочитать схему БД: {e}",
            ) from e

    allowed = allowed_table_set()
    guard_warnings: list[str] = []

    try:
        raw_sql, explanation, _excerpt = await generate_sql(body.question, tables)
        sql, w = validate_and_prepare_sql(
            raw_sql,
            settings.QUERY_MAX_ROWS,
            allowed,
        )
        guard_warnings.extend(w)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка LLM: {e}",
        ) from e

    engine = get_engine()

    try:
        cols, rows = execute_select(
            engine, sql, timeout_ms=settings.QUERY_TIMEOUT_MS
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка выполнения SQL: {e}",
        ) from e

    chart_spec, chart_payload = build_chart(cols, rows)

    return AskResponse(
        question=body.question,
        sql=sql,
        explanation=explanation,
        columns=cols,
        rows=rows,
        row_count=len(rows),
        chart=chart_spec,
        chart_payload=chart_payload,
        guard_warnings=guard_warnings,
    )


@router.post("/ask-async", response_model=AskAsyncResponse)
async def ask_async_route(
    body: QuestionRequest,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID пользователя (проставляет BFF из JWT)"),
):
    """
    Асинхронный сценарий: задача в RabbitMQ → ML SQL generator → результат в очередь и в nl_sql_jobs.
    Клиент подписывается по WebSocket на комнату job:<job_id> и получает nl_sql_result.
    """
    settings = get_settings()
    cached = schema_cache.get_cached(settings.SCHEMA_CACHE_TTL_SECONDS)
    tables = cached
    if tables is None:
        engine = get_engine()
        try:
            tables = introspect_public(engine)
            schema_cache.set_cached(tables)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Не удалось прочитать схему БД: {e}",
            ) from e

    template_key, _ = resolve_template(body.question)
    jid = create_job(
        user_id=x_user_id,
        question=body.question.strip(),
        template_key=template_key,
    )

    payload = {
        "job_id": str(jid),
        "user_id": x_user_id,
        "question": body.question.strip(),
        "template_key": template_key,
        "schema_tables": [t.model_dump() for t in tables],
    }
    try:
        await rabbit_publish.publish_generate_request(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Очередь недоступна: {e}",
        ) from e

    return AskAsyncResponse(
        job_id=str(jid),
        status="pending",
        template_key=template_key,
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_route(
    job_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    data = get_job(job_id, user_id=x_user_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return JobStatusResponse(**data)
