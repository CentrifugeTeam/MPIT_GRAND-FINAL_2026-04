from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuestionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Покажи выручку по месяцам за 2025",
                "max_rows": 1000,
                "analytics_source_key": "main-db",
            }
        }
    )
    question: str = Field(..., min_length=1, description="Вопрос на естественном языке")
    max_rows: Optional[int] = Field(
        None,
        ge=1,
        le=50_000_000,
        description="Лимит строк в guard (LIMIT). Не указано — без принудительного LIMIT.",
    )
    analytics_source_key: Optional[str] = Field(
        None,
        description="Ключ источника данных (для согласованности с NL-чатом); опционально.",
    )

    @model_validator(mode="after")
    def _clamp_max_rows_to_env_cap(self):
        from app.core.config import get_settings

        if self.max_rows is not None:
            cap = max(1, int(get_settings().GLOBAL_MAX_ROWS))
            if self.max_rows > cap:
                self.max_rows = cap
        return self


class ColumnInfo(BaseModel):
    name: str = Field(..., description="Имя колонки")
    data_type: str = Field(..., description="SQL-тип")
    enum_values: Optional[list[str]] = Field(
        default=None,
        description="Допустимые значения для enum-типов",
    )


class TableSchema(BaseModel):
    name: str = Field(..., description="Имя таблицы в public")
    columns: list[ColumnInfo] = Field(default_factory=list, description="Колонки")


class SchemaResponse(BaseModel):
    tables: list[TableSchema] = Field(default_factory=list, description="Таблицы public")
    cached: bool = Field(False, description="True если ответ из кэша analytics-service")


class GlossaryMatchItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    definition: str = ""


class QueryQualityRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Топ клиентов по выручке",
                "sql": "SELECT customer_id, SUM(amount) FROM orders GROUP BY 1",
                "interpretation_warnings": ["не указан период"],
            },
        },
    )
    question: str = Field(..., min_length=1, description="Формулировка вопроса")
    sql: Optional[str] = Field(default=None, description="Сгенерированный SQL (опционально)")
    interpretation_warnings: Optional[list[str]] = Field(
        default=None,
        description="Предупреждения из interpret",
    )


class QueryQualityResponse(BaseModel):
    summary: str = Field("", description="Краткий вывод LLM")
    risks: list[str] = Field(default_factory=list, description="Риски или неясности")
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Уточняющие вопросы",
    )
    suggested_sql_hints: str = Field("", description="Подсказки по формулировке/SQL")


class InterpretQuestionResponse(BaseModel):
    """Разбор вопроса + глоссарий для NL-чата без постановки sql_job (как начало ask-async)."""

    interpretation_confidence: float = Field(
        ...,
        ge=0,
        le=1,
    )
    interpretation_warnings: list[str] = Field(default_factory=list)
    interpretation_suggestions: list[str] = Field(default_factory=list)
    glossary_matches: list[GlossaryMatchItem] = Field(default_factory=list)
    glossary_context: Optional[str] = Field(
        default=None,
        description="Текст для LLM генератора SQL (как в ask-async).",
    )


class AnalyticsHistoryItem(BaseModel):
    """Единая строка истории: классическая задача SQL или NL-чат."""

    model_config = ConfigDict(extra="ignore")

    entry_kind: Literal["sql_job", "nl_chat"]
    sort_at: datetime
    job_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    question: str = ""
    max_rows: Optional[int] = None
    template_key: Optional[str] = None
    status: Optional[str] = None
    sql: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    chat_title: Optional[str] = None
    message_count: Optional[int] = None
    chat_type: Optional[Literal["chat"]] = None


class AnalyticsHistoryResponse(BaseModel):
    items: list[AnalyticsHistoryItem]
    total: int


class CreateNlChatResponse(BaseModel):
    conversation_id: str
    created_at: datetime


class NlChatTitlePatch(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"title": "Отчет по выручке"}})
    title: str = Field(..., min_length=1, max_length=500)


class CreateNlChatBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_type": "chat",
            }
        }
    )
    chat_type: Literal["chat"] = "chat"


class NlChatMessageApi(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    role: str
    payload: dict[str, Any]
    created_at: datetime
    client_message_id: Optional[str] = None


class NlChatTranscriptResponse(BaseModel):
    items: list[NlChatMessageApi]


class NlChatDeleteMessagesBody(BaseModel):
    message_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Идентификаторы сообщений: UUID строки в БД или client_message_id",
    )


class NlChatDeleteMessagesResponse(BaseModel):
    deleted_message_ids: list[str]
    deleted_count: int


class NlChatDeleteTailBody(BaseModel):
    from_message_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="UUID строки или client_message_id первого удаляемого сообщения; далее до конца ленты.",
    )


class NlChatSyncAck(BaseModel):
    """Ответ внутреннего sync-эндпоинта."""

    ok: Literal[True] = Field(True, description="Сообщение принято и записано")


class NlInternalChatSyncBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "action": "assistant_message",
                "user_id": "00000000-0000-0000-0000-000000000001",
                "conversation_id": "11111111-1111-1111-1111-111111111111",
                "client_message_id": "msg-123",
                "payload": {"text": "Готово, отчет сформирован."},
            }
        }
    )
    action: Literal["user_message", "assistant_message", "system_message"]
    user_id: str
    conversation_id: str
    client_message_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
