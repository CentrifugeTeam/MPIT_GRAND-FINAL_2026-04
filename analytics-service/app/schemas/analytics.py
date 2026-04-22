from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    enum_values: Optional[list[str]] = None


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnInfo]


class SchemaResponse(BaseModel):
    tables: list[TableSchema]
    cached: bool = False


class GlossaryMatchItem(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    definition: str = ""


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


class NlChatTranscriptResponse(BaseModel):
    items: list[NlChatMessageApi]


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
