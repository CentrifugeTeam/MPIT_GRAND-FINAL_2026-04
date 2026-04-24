import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.auth import get_current_user
from app.schemas.openapi_analytics import (
    ChatInviteAnswerBody,
    ChatInviteAnswerResponse,
    CloneSharedChatResponse,
    NlChatSessionMetaResponse,
    ChatSuggestionsResponse,
    AllowedDataSourceKeysResponse,
    AnalyticsHistoryResponse,
    ChatInvitesListResponse,
    CreateChatInvitesBody,
    CreateNlChatBody,
    CreateNlChatResponse,
    DataSourcesListResponse,
    DataSourcePublic,
    InterpretQuestionResponse,
    NlChatTranscriptResponse,
    QueryQualityResponse,
)
from app.services.analytics_service import AnalyticsProxy
from app.services.nl_chat_pdf import build_single_assistant_message_pdf_bytes
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.notification_realtime import publish_notification_touch
from app.schemas.notification import NotificationCreate, NotificationType

logger = logging.getLogger(__name__)

router = APIRouter()
_proxy = AnalyticsProxy()
_auth_proxy = AuthService()
_notification_proxy = NotificationService()

_AUTH_DESC = (
    "Требуется заголовок Authorization: Bearer с access-токеном; "
    "BFF прокидывает X-User-Id и X-User-Role в analytics."
)


class QueryQualityBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Сколько заказов за январь?",
                "sql": "SELECT COUNT(*) FROM orders WHERE ...",
                "interpretation_warnings": ["не указан год"],
            }
        },
    )
    question: str = Field(..., min_length=1, description="Формулировка вопроса пользователя")
    sql: str | None = Field(default=None, description="SQL после генерации (опционально)")
    interpretation_warnings: list[str] | None = Field(
        default=None,
        description="Предупреждения из /interpret-question",
    )


class InterpretQuestionBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Покажи выручку по месяцам за 2025",
                "max_rows": 1000,
                "analytics_source_key": "main-db",
            },
        },
    )
    question: str = Field(..., min_length=1, description="Текст вопроса на естественном языке")
    max_rows: int | None = Field(
        default=None,
        ge=1,
        description="Желаемый лимит строк LIMIT (сервер может урезать по GLOBAL_MAX_ROWS)",
    )
    analytics_source_key: str | None = Field(
        default=None,
        description="Ключ источника; если не указан — дефолтный из настроек analytics",
    )


class PatchChatTitleBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"title": "Еженедельный отчет"}})
    title: str = Field(..., min_length=1, max_length=500, description="Новый заголовок чата")


class DataSourceCreateBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "main-db",
                "display_name": "Warehouse (main_db)",
                "database_url": "postgresql://postgres:postgres@main-db:5432/main_db",
                "set_as_default": True,
            },
        },
    )
    key: str = Field(..., min_length=1, max_length=64, description="Уникальный ключ источника")
    display_name: str = Field(..., description="Отображаемое имя")
    database_url: str = Field(..., min_length=8, description="Postgres DSN для SELECT")
    set_as_default: bool = Field(
        default=False,
        description="Сделать источником по умолчанию после создания",
    )


class DataSourcePatchBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "Warehouse (updated)",
                "database_url": "postgresql://postgres:postgres@main-db:5432/main_db",
                "is_default": False,
            },
        },
    )
    display_name: str | None = Field(default=None, description="Новое отображаемое имя")
    database_url: str | None = Field(default=None, description="Новый DSN")
    is_default: bool | None = Field(default=None, description="Пометить как default")


class DefaultSourceBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"key": "main-db"}})
    key: str = Field(..., min_length=1, max_length=64, description="Ключ существующего источника")


def _require_admin(current_user: dict) -> None:
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только роль ADMIN может менять источники данных",
        )


@router.post(
    "/interpret-question",
    response_model=InterpretQuestionResponse,
    summary="Разбор вопроса и глоссарий",
    description=(
        "Лёгкий разбор без SQL и без постановки задачи. "
        "Требуется политика доступа к источнику для роли пользователя. "
        + _AUTH_DESC
    ),
    responses={
        401: {"description": "Нет или просрочен JWT"},
        403: {"description": "Нет политики доступа к источнику"},
    },
)
async def interpret_question(
    body: InterpretQuestionBody,
    current_user: dict = Depends(get_current_user),
) -> InterpretQuestionResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.interpret_question(
        body.model_dump(exclude_none=True),
        user_id=uid,
        user_role=role,
    )
    return InterpretQuestionResponse.model_validate(raw)


@router.post(
    "/query-quality",
    response_model=QueryQualityResponse,
    summary="Оценка качества вопроса/SQL (LLM, без выполнения)",
    description="Анализ рисков и уточняющих вопросов; секреты в тексте маскируются на стороне analytics. " + _AUTH_DESC,
    responses={401: {"description": "Нет или просрочен JWT"}},
)
async def query_quality(
    body: QueryQualityBody,
    current_user: dict = Depends(get_current_user),
) -> QueryQualityResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.query_quality(
        body.model_dump(exclude_none=True),
        user_id=uid,
        user_role=role,
    )
    return QueryQualityResponse.model_validate(raw)


@router.get(
    "/chat-suggestions",
    response_model=ChatSuggestionsResponse,
    summary="FAQ-подсказки аналитического чата",
    description="Серверные темы и вопросы для suggestion-блока. " + _AUTH_DESC,
)
async def list_chat_suggestions(
    source_key: str | None = Query(
        None,
        description="Ключ активного источника данных",
    ),
    locale: str = Query(
        "ru",
        min_length=2,
        max_length=8,
        description="Локаль набора подсказок",
    ),
    current_user: dict = Depends(get_current_user),
) -> ChatSuggestionsResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.list_chat_suggestions(
        uid,
        source_key=source_key,
        locale=locale,
        user_role=role,
    )
    return ChatSuggestionsResponse.model_validate(raw)


@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить всю историю пользователя",
    description="Удаляет nl_sql_jobs и NL-чаты текущего пользователя на платформе. " + _AUTH_DESC,
)
async def delete_all_history(
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_all_history(uid, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/history",
    response_model=AnalyticsHistoryResponse,
    summary="Объединённая история (SQL-задачи и NL-чаты)",
    description="Постраничный список. " + _AUTH_DESC,
)
async def get_job_history(
    limit: int = Query(
        50,
        ge=1,
        le=200,
        description="Размер страницы",
    ),
    offset: int = Query(0, ge=0, description="Смещение с начала"),
    current_user: dict = Depends(get_current_user),
) -> AnalyticsHistoryResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.get_history(uid, limit=limit, offset=offset, user_role=role)
    return AnalyticsHistoryResponse.model_validate(raw)


@router.post(
    "/chats",
    response_model=CreateNlChatResponse,
    summary="Создать пустой NL-чат",
    description="Создаёт сессию типа chat. Тело опционально (chat_type). " + _AUTH_DESC,
)
async def create_nl_chat(
    body: CreateNlChatBody | None = Body(None),
    current_user: dict = Depends(get_current_user),
) -> CreateNlChatResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    payload = body.model_dump(exclude_none=True) if body else {}
    raw = await _proxy.create_nl_chat(uid, user_role=role, json_body=payload or None)
    return CreateNlChatResponse.model_validate(raw)


@router.post(
    "/chats/{conversation_id}/share-invites",
    response_model=ChatInvitesListResponse,
    summary="Создать инвайты на чат по email",
    description="Список email; совместный просмотр. Уведомление с названием чата и email владельца.",
)
async def create_chat_share_invites(
    conversation_id: str,
    body: CreateChatInvitesBody,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> ChatInvitesListResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    email = str(current_user.get("email") or "").strip()
    raw = await _proxy.create_chat_invites(
        uid,
        conversation_id,
        emails=list(body.emails),
        user_role=role,
        user_email=email,
    )
    for invite in raw.get("items", []):
        invitee_email = str(invite.get("invitee_email") or "").strip().lower()
        if not invitee_email:
            continue
        try:
            invitee_user = await _auth_proxy.get_user_by_email(invitee_email)
            invitee_id = str(invitee_user.get("uuid") or "")
            if not invitee_id:
                continue
            chat_title = (invite.get("chat_title") or "").strip() or "Chat"
            owner_disp = (invite.get("owner_email") or email or "").strip() or "Someone"
            await _notification_proxy.send_notification_to_queue(
                invitee_id,
                NotificationCreate(
                    type=NotificationType.CHAT_INVITE,
                    title=chat_title,
                    message=f"{owner_disp} invited you to collaborate on this chat.",
                    payload={
                        "invite_id": invite.get("invite_id"),
                        "conversation_id": conversation_id,
                        "owner_user_id": uid,
                        "owner_email": owner_disp,
                        "chat_title": chat_title,
                    },
                ).model_dump(),
            )
            await publish_notification_touch(
                getattr(request.app.state, "redis_client", None), invitee_id
            )
        except Exception as e:
            logger.warning(
                "chat_invite notification failed for %s: %s",
                invitee_email,
                e,
                exc_info=True,
            )
    return ChatInvitesListResponse.model_validate(raw)


@router.post(
    "/chats/{conversation_id}/clone-for-me",
    response_model=CloneSharedChatResponse,
    summary="Склонировать расшаренный чат в свой",
)
async def clone_shared_chat(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> CloneSharedChatResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    em = str(current_user.get("email") or "")
    raw = await _proxy.clone_shared_chat(uid, conversation_id, user_role=role, user_email=em)
    return CloneSharedChatResponse.model_validate(raw)


@router.get(
    "/chats/{conversation_id}/meta",
    response_model=NlChatSessionMetaResponse,
    summary="Метаданные NL-чата и роль доступа",
)
async def get_nl_chat_meta(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> NlChatSessionMetaResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    em = str(current_user.get("email") or "")
    raw = await _proxy.get_nl_chat_meta(uid, conversation_id, user_role=role, user_email=em)
    return NlChatSessionMetaResponse.model_validate(raw)


@router.get(
    "/chat-invites",
    response_model=ChatInvitesListResponse,
    summary="Список входящих инвайтов на чаты",
)
async def list_chat_invites(
    current_user: dict = Depends(get_current_user),
) -> ChatInvitesListResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    email = str(current_user.get("email") or "")
    raw = await _proxy.list_chat_invites(uid, user_role=role, user_email=email)
    return ChatInvitesListResponse.model_validate(raw)


@router.post(
    "/chat-invites/{invite_id}/answer",
    response_model=ChatInviteAnswerResponse,
    summary="Принять или отклонить инвайт на чат",
)
async def answer_chat_invite(
    invite_id: str,
    body: ChatInviteAnswerBody,
    current_user: dict = Depends(get_current_user),
) -> ChatInviteAnswerResponse:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    email = str(current_user.get("email") or "")
    raw = await _proxy.answer_chat_invite(
        uid,
        invite_id,
        body.decision,
        user_role=role,
        user_email=email,
    )
    return ChatInviteAnswerResponse.model_validate(raw)


@router.get(
    "/chats/{conversation_id}/messages",
    response_model=NlChatTranscriptResponse,
    summary="Сообщения NL-чата",
    description="Транскрипт по conversation_id. 404 если чат не найден или чужой. " + _AUTH_DESC,
    responses={404: {"description": "Чат не найден"}},
)
async def get_nl_chat_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> NlChatTranscriptResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.get_nl_chat_messages(uid, conversation_id, user_role=role)
    return NlChatTranscriptResponse.model_validate(raw)


@router.get(
    "/chats/{conversation_id}/export/pdf",
    summary="Экспорт одного ответа ассистента в PDF",
    description=(
        "Параметр message_id — id сообщения assistant из GET .../messages. "
        "В PDF: вопрос пользователя (предыдущее user-сообщение) как заголовок, ответ без reasoning, "
        "при наличии — график и таблица. Имя файла — по тексту вопроса (filename* UTF-8). "
        + _AUTH_DESC
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF-файл",
        },
        400: {"description": "message_id не указывает на assistant"},
        401: {"description": "Нет или просрочен JWT"},
        404: {"description": "Чат или сообщение не найдены"},
    },
)
async def export_nl_chat_pdf(
    conversation_id: str,
    message_id: str = Query(..., min_length=1, description="UUID сообщения assistant"),
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = str(current_user.get("uuid") or "")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.get_nl_chat_messages(uid, conversation_id, user_role=role)
    try:
        pdf_bytes, disposition = build_single_assistant_message_pdf_bytes(raw, message_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сообщение не найдено в этом чате",
        ) from None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e) or "message_id должен указывать на сообщение ассистента",
        ) from e
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": disposition},
    )


@router.patch(
    "/chats/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Переименовать NL-чат",
    description="PATCH заголовка сессии. " + _AUTH_DESC,
)
async def patch_nl_chat_title(
    conversation_id: str,
    body: PatchChatTitleBody = Body(...),
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title required")
    role = str(current_user.get("role") or "USER")
    await _proxy.patch_nl_chat_title(uid, conversation_id, title, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/chats/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить NL-чат",
    description="Удаляет сессию и сообщения. " + _AUTH_DESC,
)
async def delete_nl_chat(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_nl_chat(uid, conversation_id, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу NL→SQL",
    description="Удаление записи nl_sql_jobs владельца. " + _AUTH_DESC,
)
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    await _proxy.delete_job(job_id, uid, user_role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/data-sources",
    response_model=DataSourcesListResponse,
    summary="Список источников данных",
    description="Публичные поля без DSN. " + _AUTH_DESC,
)
async def list_data_sources(
    _user: dict = Depends(get_current_user),
) -> DataSourcesListResponse:
    raw = await _proxy.list_data_sources()
    return DataSourcesListResponse.model_validate(raw)


@router.get(
    "/data-sources/allowed-keys",
    response_model=AllowedDataSourceKeysResponse,
    summary="Ключи источников, доступных текущей роли",
    description="По политикам analytics; для шаблонов отчётов и выбора источника. " + _AUTH_DESC,
)
async def list_allowed_data_source_keys(
    current_user: dict = Depends(get_current_user),
) -> AllowedDataSourceKeysResponse:
    uid = current_user.get("uuid")
    role = str(current_user.get("role") or "USER")
    raw = await _proxy.list_allowed_analytics_source_keys(uid, user_role=role)
    return AllowedDataSourceKeysResponse(keys=raw)


@router.post(
    "/data-sources",
    response_model=DataSourcePublic,
    summary="Создать источник данных (ADMIN)",
    description="Прокси в analytics; при настроенном токене нужен X-Analytics-Sources-Write-Token на analytics. " + _AUTH_DESC,
    responses={403: {"description": "Не ADMIN или отказ analytics"}},
)
async def create_data_source(
    body: DataSourceCreateBody,
    current_user: dict = Depends(get_current_user),
) -> DataSourcePublic:
    _require_admin(current_user)
    raw = await _proxy.create_data_source(body.model_dump(exclude_none=True))
    return DataSourcePublic.model_validate(raw)


@router.patch(
    "/data-sources/{source_key}",
    response_model=DataSourcePublic,
    summary="Изменить источник данных (ADMIN)",
    description="Частичное обновление. " + _AUTH_DESC,
)
async def patch_data_source(
    source_key: str,
    body: DataSourcePatchBody,
    current_user: dict = Depends(get_current_user),
) -> DataSourcePublic:
    _require_admin(current_user)
    raw = await _proxy.patch_data_source(source_key, body.model_dump(exclude_none=True))
    return DataSourcePublic.model_validate(raw)


@router.delete(
    "/data-sources/{source_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить источник данных (ADMIN)",
    description="Удаление ключа источника на платформе. " + _AUTH_DESC,
)
async def delete_data_source(
    source_key: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    await _proxy.delete_data_source(source_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/data-sources/default",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Назначить источник по умолчанию (ADMIN)",
    description="Тело: {\"key\": \"...\"}. " + _AUTH_DESC,
)
async def put_default_data_source(
    body: DefaultSourceBody,
    current_user: dict = Depends(get_current_user),
) -> Response:
    _require_admin(current_user)
    await _proxy.put_default_data_source(body.model_dump(exclude_none=True))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
