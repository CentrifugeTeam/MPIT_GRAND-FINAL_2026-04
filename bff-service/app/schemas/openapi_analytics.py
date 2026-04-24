# Синхронизировать поля с analytics-service/app/schemas/analytics.py и data_sources (ответы list/create/patch).
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GlossaryMatchItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = Field(default=None, description="Идентификатор записи глоссария")
    title: Optional[str] = Field(default=None, description="Краткое название метрики")
    category: Optional[str] = Field(default=None, description="Категория")
    definition: str = Field("", description="Определение для LLM")


class InterpretQuestionResponse(BaseModel):
    interpretation_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Уверенность эвристического разбора вопроса (0–1)",
    )
    interpretation_warnings: list[str] = Field(
        default_factory=list,
        description="Предупреждения о неоднозначности",
    )
    interpretation_suggestions: list[str] = Field(
        default_factory=list,
        description="Подсказки по уточнению формулировки",
    )
    glossary_matches: list[GlossaryMatchItem] = Field(
        default_factory=list,
        description="Совпадения с корпоративным глоссарием",
    )
    glossary_context: Optional[str] = Field(
        default=None,
        description="Текст глоссария для промпта генератора SQL",
    )


class QueryQualityResponse(BaseModel):
    summary: str = Field("", description="Краткая оценка формулировки/рисков")
    risks: list[str] = Field(default_factory=list, description="Риски или пробелы")
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Уточняющие вопросы пользователю",
    )
    suggested_sql_hints: str = Field(
        "",
        description="Подсказки по перефразированию без выполнения SQL",
    )


class AnalyticsHistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entry_kind: Literal["sql_job", "nl_chat"] = Field(
        ...,
        description="Тип записи: классическая NL→SQL задача или NL-чат",
    )
    sort_at: datetime = Field(..., description="Время для сортировки списка")
    job_id: Optional[str] = Field(default=None, description="ID задачи (для sql_job)")
    conversation_id: Optional[str] = Field(default=None, description="ID чата (для nl_chat)")
    user_id: Optional[str] = Field(default=None, description="Владелец")
    question: str = Field("", description="Исходный вопрос")
    max_rows: Optional[int] = Field(default=None, description="Лимит строк SQL")
    template_key: Optional[str] = None
    status: Optional[str] = Field(default=None, description="Статус задачи")
    sql: Optional[str] = Field(default=None, description="Сгенерированный SQL")
    explanation: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict[str, Any]] = Field(default=None, description="Результат SELECT (JSON)")
    created_at: datetime
    updated_at: Optional[datetime] = None
    chat_title: Optional[str] = Field(default=None, description="Заголовок чата")
    message_count: Optional[int] = Field(default=None, description="Число сообщений в чате")
    chat_type: Optional[Literal["chat"]] = None


class AnalyticsHistoryResponse(BaseModel):
    items: list[AnalyticsHistoryItem] = Field(..., description="Страница истории")
    total: int = Field(..., description="Общее число записей")


class CreateNlChatBody(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"chat_type": "chat"}},
    )
    chat_type: Literal["chat"] = Field(
        default="chat",
        description="Тип сессии (сейчас только chat)",
    )


class CreateNlChatResponse(BaseModel):
    conversation_id: str = Field(..., description="UUID новой сессии NL-чата")
    created_at: datetime = Field(..., description="Время создания")


class NlChatMessageApi(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="ID сообщения")
    role: str = Field(..., description="user | assistant | system")
    payload: dict[str, Any] = Field(default_factory=dict, description="Тело сообщения (JSON)")
    created_at: datetime


class NlChatTranscriptResponse(BaseModel):
    items: list[NlChatMessageApi] = Field(
        default_factory=list,
        description="Сообщения в хронологическом порядке",
    )


class DataSourcePublic(BaseModel):
    key: str = Field(..., description="Ключ источника для analytics_source_key")
    display_name: str = Field(..., description="Подпись в UI")
    is_default: bool = Field(..., description="Источник по умолчанию")


class DataSourcesListResponse(BaseModel):
    items: list[DataSourcePublic] = Field(default_factory=list)
    default_key: Optional[str] = Field(
        default=None,
        description="Ключ источника по умолчанию",
    )


class AllowedDataSourceKeysResponse(BaseModel):
    keys: list[str] = Field(
        default_factory=list,
        description="Источники, разрешённые политикой для X-User-Role",
    )


class ChatSuggestionTopic(BaseModel):
    topic_key: str = Field(..., description="Стабильный ключ темы")
    topic_label: str = Field(..., description="Подпись темы для UI")
    questions: list[str] = Field(
        default_factory=list,
        min_length=4,
        max_length=4,
        description="Ровно 4 вопроса на тему",
    )


class ChatSuggestionsResponse(BaseModel):
    items: list[ChatSuggestionTopic] = Field(
        default_factory=list,
        max_length=5,
        description="До 5 тем FAQ",
    )
