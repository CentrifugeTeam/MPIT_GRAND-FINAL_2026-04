import uuid

from fastapi import APIRouter, Header, HTTPException, Query, Response, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings
from app.schemas.analytics import (
    AskAsyncResponse,
    AskResponse,
    ExecuteSqlRequest,
    ExecuteSqlResponse,
    GenerateSqlResponse,
    GlossaryListResponse,
    GlossaryMatchItem,
    JobHistoryItem,
    JobHistoryResponse,
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
from app.services.metrics_glossary import (
    format_glossary_for_llm,
    get_version,
    match_entries_for_question,
    public_match_models,
    search_entries,
)
from app.services.question_interpretation import analyze_question
from app.services.template_parser import resolve_template
from app.services.job_store import (
    create_job,
    reset_job_for_rerun,
    delete_all_jobs_for_user,
    delete_job,
    get_job,
    list_jobs_for_user,
)
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

    allowed = allowed_table_set()
    try:
        raw_sql, explanation, excerpt = await generate_sql(body.question, tables)
        sql, _gw = validate_and_prepare_sql(
            raw_sql,
            body.max_rows,
            allowed,
            schema_tables=tables,
        )
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
    tables_for_guard = schema_cache.get_cached(settings.SCHEMA_CACHE_TTL_SECONDS)
    if tables_for_guard is None:
        engine = get_engine()
        try:
            tables_for_guard = introspect_public(engine)
            schema_cache.set_cached(tables_for_guard)
        except Exception:
            tables_for_guard = None

    try:
        sql, warnings = validate_and_prepare_sql(
            body.sql,
            body.max_rows,
            allowed,
            schema_tables=tables_for_guard,
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
            body.max_rows,
            allowed,
            schema_tables=tables,
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


@router.get("/glossary", response_model=GlossaryListResponse)
async def get_glossary_route(
    q: str | None = Query(None, description="Поиск по названию, синонимам, описанию"),
    limit: int = Query(500, ge=1, le=2000),
):
    """Семантический слой: полный глоссарий метрик или фильтр по подстроке."""
    entries = search_entries(q, limit=limit)
    return GlossaryListResponse(version=get_version(), total=len(entries), entries=entries)


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

    qtext = body.question.strip()
    template_key, _ = resolve_template(qtext)
    interp = analyze_question(qtext)
    gloss_matches = match_entries_for_question(qtext)
    glossary_ctx = format_glossary_for_llm(gloss_matches)
    interpretation_payload = {
        "confidence": interp.confidence,
        "warnings": interp.warnings,
        "suggestions": interp.suggestions,
    }

    jid = create_job(
        user_id=x_user_id,
        question=qtext,
        template_key=template_key,
        max_rows=body.max_rows,
    )

    payload = {
        "job_id": str(jid),
        "user_id": x_user_id,
        "question": qtext,
        "template_key": template_key,
        "schema_tables": [t.model_dump() for t in tables],
        "max_rows": body.max_rows,
        "glossary_context": glossary_ctx or None,
        "interpretation": interpretation_payload,
    }
    try:
        await rabbit_publish.publish_generate_request(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Очередь недоступна: {e}",
        ) from e

    gm = [GlossaryMatchItem(**x) for x in public_match_models(gloss_matches)]
    return AskAsyncResponse(
        job_id=str(jid),
        status="pending",
        template_key=template_key,
        interpretation_confidence=interp.confidence,
        interpretation_warnings=interp.warnings,
        interpretation_suggestions=interp.suggestions,
        glossary_matches=gm,
    )


@router.post("/jobs/{job_id}/rerun", response_model=AskAsyncResponse)
async def rerun_job_route(
    job_id: uuid.UUID,
    body: QuestionRequest,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID пользователя (проставляет BFF из JWT)"),
):
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

    qtext = body.question.strip()
    template_key, _ = resolve_template(qtext)
    interp = analyze_question(qtext)
    gloss_matches = match_entries_for_question(qtext)
    glossary_ctx = format_glossary_for_llm(gloss_matches)
    interpretation_payload = {
        "confidence": interp.confidence,
        "warnings": interp.warnings,
        "suggestions": interp.suggestions,
    }

    ok = reset_job_for_rerun(
        job_id=job_id,
        user_id=x_user_id,
        question=qtext,
        template_key=template_key,
        max_rows=body.max_rows,
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    payload = {
        "job_id": str(job_id),
        "user_id": x_user_id,
        "question": qtext,
        "template_key": template_key,
        "schema_tables": [t.model_dump() for t in tables],
        "max_rows": body.max_rows,
        "glossary_context": glossary_ctx or None,
        "interpretation": interpretation_payload,
    }
    try:
        await rabbit_publish.publish_generate_request(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Очередь недоступна: {e}",
        ) from e

    gm = [GlossaryMatchItem(**x) for x in public_match_models(gloss_matches)]
    return AskAsyncResponse(
        job_id=str(job_id),
        status="pending",
        template_key=template_key,
        interpretation_confidence=interp.confidence,
        interpretation_warnings=interp.warnings,
        interpretation_suggestions=interp.suggestions,
        glossary_matches=gm,
    )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_history_route(
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    delete_all_jobs_for_user(x_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/history", response_model=JobHistoryResponse)
async def list_job_history_route(
    x_user_id: str = Header(..., alias="X-User-Id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    rows, total = list_jobs_for_user(x_user_id, limit=limit, offset=offset)
    return JobHistoryResponse(
        items=[JobHistoryItem(**row) for row in rows],
        total=total,
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


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_route(
    job_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    ok = delete_job(job_id, x_user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
