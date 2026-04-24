import logging
import uuid

from fastapi import APIRouter, Header, HTTPException, Query, Response, status

from app.core.config import get_settings
from app.schemas.analytics import (
    AnalyticsHistoryItem,
    AnalyticsHistoryResponse,
    ChatSuggestionsResponse,
    CreateNlChatBody,
    CreateNlChatResponse,
    GlossaryMatchItem,
    InterpretQuestionResponse,
    NlChatDeleteMessagesBody,
    NlChatDeleteMessagesResponse,
    NlChatDeleteTailBody,
    NlChatMessageApi,
    NlChatSyncAck,
    NlChatTitlePatch,
    NlChatTranscriptResponse,
    NlInternalChatSyncBody,
    QuestionRequest,
    QueryQualityRequest,
    QueryQualityResponse,
    SchemaResponse,
    TableSchema,
)
from app.services.db_schema import introspect_public
from app.services import schema_cache
from app.services.metrics_glossary import (
    format_glossary_for_llm,
    match_entries_for_question,
    public_match_models,
)
from app.services.question_interpretation import analyze_question
from app.services.sensitive_redaction import redact_sensitive_text
from app.services.access_policy import admin_bypass, filter_schema_tables
from app.services import access_policy_store as access_policy_store_mod
from app.services.chat_store import (
    append_message,
    create_empty_session,
    delete_all_sessions_for_user,
    delete_messages_by_keys,
    delete_messages_from_anchor_inclusive,
    delete_session,
    ensure_session,
    get_session_for_user,
    list_messages,
    update_session_title,
)
from app.services.history_unified import list_unified_history
from app.services.job_store import delete_all_jobs_for_user, delete_job
from app.services.chat_suggestions_store import list_chat_suggestions

router = APIRouter()
logger = logging.getLogger("analytics.api")


def _slim_assistant_payload_for_db(p: dict) -> dict:
    """Ограничиваем размер JSONB для сообщений ассистента в чате."""
    out = dict(p)
    rows = out.get("rows")
    if isinstance(rows, list) and len(rows) > 200:
        out["rows"] = rows[:200]
    cp = out.get("chart_payload")
    if isinstance(cp, dict):
        cp2 = dict(cp)
        if cp2.get("type") in ("bar", "line"):
            cp2.pop("rows", None)
        trows = cp2.get("rows")
        if isinstance(trows, list) and len(trows) > 200:
            cp2["rows"] = trows[:200]
        out["chart_payload"] = cp2
    return out


@router.get(
    "/chat-suggestions",
    response_model=ChatSuggestionsResponse,
    summary="FAQ-подсказки для аналитического чата",
    description="Серверные темы и вопросы (до 5 тем, по 4 вопроса), источник учитывает source_key и fallback на default.",
)
async def get_chat_suggestions_route(
    source_key: str | None = Query(
        None,
        description="Ключ источника данных; если нет данных, используется fallback на default source.",
    ),
    locale: str = Query(
        "ru",
        min_length=2,
        max_length=8,
        description="Локаль подборки подсказок.",
    ),
):
    items = list_chat_suggestions(source_key=source_key, locale=locale)
    return ChatSuggestionsResponse(items=items)


@router.get(
    "/schema",
    response_model=SchemaResponse,
    summary="Схема public выбранного источника",
    description="С учётом политики доступа (колонки могут быть отфильтрованы). ADMIN — полная схема.",
)
async def get_schema(
    refresh: bool = Query(False, description="Обновить кэш схемы из БД"),
    source_key: str | None = Query(
        None,
        description="Ключ источника из /data-sources; по умолчанию — default в БД",
    ),
    x_user_role: str | None = Header(
        None,
        alias="X-User-Role",
        description="Роль пользователя (обычно проставляет BFF из JWT)",
    ),
):
    from app.services.analytics_db import get_analytics_engine
    from app.db.platform_session import PlatformSessionLocal

    settings = get_settings()
    sk = (source_key or "").strip() or None
    if not sk:
        sk = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip() or None
    role = (x_user_role or "USER").strip().upper()
    with PlatformSessionLocal() as pdb:
        pol = access_policy_store_mod.resolve_effective_policy(
            user_role=role, source_key=sk, db=pdb
        )
    if pol is None and not admin_bypass(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет политики доступа к этому источнику для вашей роли",
        )

    cached = schema_cache.get_cached(settings.SCHEMA_CACHE_TTL_SECONDS, sk)
    if cached is not None and not refresh:
        tables_out = list(cached)
        if pol and not admin_bypass(role):
            raw = [t.model_dump() for t in tables_out]
            tables_out = [
                TableSchema.model_validate(x)
                for x in filter_schema_tables(raw, pol)
            ]
        return SchemaResponse(tables=tables_out, cached=True)

    engine = get_analytics_engine(sk)
    try:
        tables = introspect_public(engine)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Не удалось прочитать схему БД: {e}",
        ) from e

    schema_cache.set_cached(tables, sk)
    tables_out = list(tables)
    if pol and not admin_bypass(role):
        raw = [t.model_dump() for t in tables_out]
        tables_out = [TableSchema.model_validate(x) for x in filter_schema_tables(raw, pol)]
    return SchemaResponse(tables=tables_out, cached=False)


@router.post(
    "/interpret-question",
    response_model=InterpretQuestionResponse,
    summary="Разбор вопроса и глоссарий (без SQL)",
    description="Без постановки sql_job. Требуется политика доступа к источнику для роли.",
)
async def interpret_question_route(
    body: QuestionRequest,
    x_user_role: str | None = Header(
        None,
        alias="X-User-Role",
        description="Роль для проверки analytics_access_policies",
    ),
):
    from app.db.platform_session import PlatformSessionLocal

    settings = get_settings()
    sk = (body.analytics_source_key or "").strip() or None
    if not sk:
        sk = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip() or None
    role = (x_user_role or "USER").strip().upper()
    with PlatformSessionLocal() as pdb:
        pol = access_policy_store_mod.resolve_effective_policy(
            user_role=role, source_key=sk, db=pdb
        )
    if pol is None and not admin_bypass(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет политики доступа к этому источнику для вашей роли",
        )

    qtext = redact_sensitive_text(body.question.strip())
    interp = analyze_question(qtext)
    gloss_matches = match_entries_for_question(qtext)
    glossary_ctx = format_glossary_for_llm(gloss_matches)
    gm = [GlossaryMatchItem(**x) for x in public_match_models(gloss_matches)]
    logger.info(
        "interpret_question role=%s source=%s confidence=%s",
        role,
        sk,
        interp.confidence,
    )
    return InterpretQuestionResponse(
        interpretation_confidence=interp.confidence,
        interpretation_warnings=interp.warnings,
        interpretation_suggestions=interp.suggestions,
        glossary_matches=gm,
        glossary_context=glossary_ctx or None,
    )


@router.post(
    "/query-quality",
    response_model=QueryQualityResponse,
    summary="LLM-оценка качества вопроса/SQL",
    description="Без выполнения SQL; текст маскируется от секретов.",
)
async def query_quality_route(
    body: QueryQualityRequest,
    x_user_role: str | None = Header(
        None,
        alias="X-User-Role",
        description="Роль (зарезервировано для будущих лимитов)",
    ),
):
    from app.services.query_quality_llm import analyze_query_quality

    _ = (x_user_role or "USER").strip().upper()
    q = redact_sensitive_text(body.question.strip())
    out = await analyze_query_quality(
        question=q,
        sql=body.sql,
        interpretation_warnings=body.interpretation_warnings,
    )
    return QueryQualityResponse(**out)


@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить историю и чаты пользователя",
    description="Очищает nl_sql_jobs и nl_chat для X-User-Id.",
)
async def delete_all_history_route(
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID пользователя"),
):
    delete_all_jobs_for_user(x_user_id)
    delete_all_sessions_for_user(x_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/history",
    response_model=AnalyticsHistoryResponse,
    summary="Объединённая история",
    description="SQL-задачи и NL-чаты одним списком.",
)
async def list_unified_history_route(
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID пользователя"),
    limit: int = Query(50, ge=1, le=200, description="Размер страницы"),
    offset: int = Query(0, ge=0, description="Смещение"),
):
    rows, total = list_unified_history(x_user_id, limit=limit, offset=offset)
    return AnalyticsHistoryResponse(
        items=[AnalyticsHistoryItem(**row) for row in rows],
        total=total,
    )


@router.post(
    "/internal/nl-chat-sync",
    response_model=NlChatSyncAck,
    summary="Внутренняя синхронизация сообщений NL-чата",
    description="Только nl-orchestrator-worker с корректным X-Chat-Sync-Token.",
    tags=["internal"],
)
async def internal_nl_chat_sync(
    body: NlInternalChatSyncBody,
    x_chat_sync_token: str = Header(
        "",
        alias="X-Chat-Sync-Token",
        description="Должен совпадать с INTERNAL_NL_CHAT_SYNC_TOKEN",
    ),
):
    token = get_settings().INTERNAL_NL_CHAT_SYNC_TOKEN
    if not token or x_chat_sync_token != token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    uid = body.user_id.strip()
    cid = body.conversation_id.strip()
    if not uid or not cid:
        raise HTTPException(status_code=400, detail="user_id and conversation_id required")
    if body.action == "user_message":
        tx = redact_sensitive_text(str(body.payload.get("text") or "").strip())
        if tx:
            ensure_session(uid, cid, title_hint=tx[:200])
            append_message(uid, cid, "user", {"text": tx}, body.client_message_id)
    elif body.action == "system_message":
        append_message(uid, cid, "system", dict(body.payload), body.client_message_id)
    elif body.action == "assistant_message":
        pl = _slim_assistant_payload_for_db(dict(body.payload))
        append_message(uid, cid, "assistant", pl, body.client_message_id)
    return NlChatSyncAck()


@router.post(
    "/chats",
    response_model=CreateNlChatResponse,
    summary="Создать пустой NL-чат",
    description="Сессия для последующих сообщений через sync или прямой API.",
)
async def create_nl_chat_route(
    body: CreateNlChatBody | None = None,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    _ = body or CreateNlChatBody()
    cid = create_empty_session(x_user_id, chat_type="chat")
    meta = get_session_for_user(x_user_id, cid)
    if not meta:
        raise HTTPException(status_code=500, detail="session create failed")
    return CreateNlChatResponse(
        conversation_id=cid,
        created_at=meta["created_at"],
    )


@router.get(
    "/chats/{conversation_id}/messages",
    response_model=NlChatTranscriptResponse,
    summary="Сообщения чата",
    description="404 если сессия не принадлежит пользователю.",
)
async def get_nl_chat_messages_route(
    conversation_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    cid = str(conversation_id)
    if get_session_for_user(x_user_id, cid) is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    rows = list_messages(x_user_id, cid)
    return NlChatTranscriptResponse(
        items=[NlChatMessageApi.model_validate(r) for r in rows],
    )


@router.post(
    "/chats/{conversation_id}/messages/delete",
    response_model=NlChatDeleteMessagesResponse,
    summary="Удалить сообщения NL-чата",
    description="По UUID строки или client_message_id; только своя сессия.",
)
async def delete_nl_chat_messages_route(
    conversation_id: uuid.UUID,
    body: NlChatDeleteMessagesBody,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    cid = str(conversation_id)
    if get_session_for_user(x_user_id, cid) is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    try:
        deleted_ui = delete_messages_by_keys(x_user_id, cid, body.message_ids)
    except ValueError:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return NlChatDeleteMessagesResponse(
        deleted_message_ids=deleted_ui,
        deleted_count=len(deleted_ui),
    )


@router.post(
    "/chats/{conversation_id}/messages/delete-tail",
    response_model=NlChatDeleteMessagesResponse,
    summary="Удалить хвост NL-чата с сообщения",
    description="Сообщение-якорь и все следующие по времени в сессии.",
)
async def delete_nl_chat_messages_tail_route(
    conversation_id: uuid.UUID,
    body: NlChatDeleteTailBody,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    cid = str(conversation_id)
    if get_session_for_user(x_user_id, cid) is None:
        raise HTTPException(status_code=404, detail="Чат не найден")
    try:
        deleted_ui = delete_messages_from_anchor_inclusive(
            x_user_id, cid, body.from_message_id
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return NlChatDeleteMessagesResponse(
        deleted_message_ids=deleted_ui,
        deleted_count=len(deleted_ui),
    )


@router.patch(
    "/chats/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Переименовать чат",
)
async def patch_nl_chat_title_route(
    conversation_id: uuid.UUID,
    body: NlChatTitlePatch,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    ok = update_session_title(x_user_id, str(conversation_id), body.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/chats/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить чат",
)
async def delete_nl_chat_route(
    conversation_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    ok = delete_session(x_user_id, str(conversation_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу NL→SQL",
)
async def delete_job_route(
    job_id: uuid.UUID,
    x_user_id: str = Header(..., alias="X-User-Id", description="UUID владельца"),
):
    ok = delete_job(job_id, x_user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
