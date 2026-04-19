from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Вопрос на естественном языке")


class ExecuteSqlRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="Только SELECT / WITH ... SELECT")


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


class GenerateSqlResponse(BaseModel):
    sql: str
    explanation: Optional[str] = None
    raw_llm_excerpt: Optional[str] = None


class ExecuteSqlResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    guard_warnings: list[str] = Field(default_factory=list)


class ChartSpec(BaseModel):
    type: Literal["line", "bar", "table"] = "table"
    x_key: Optional[str] = None
    series: list[dict[str, str]] = Field(default_factory=list)


class AskResponse(BaseModel):
    question: str
    sql: str
    explanation: Optional[str] = None
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    chart: ChartSpec
    chart_payload: dict[str, Any]
    guard_warnings: list[str] = Field(default_factory=list)


class ErrorDetail(BaseModel):
    detail: str


class AskAsyncResponse(BaseModel):
    job_id: str
    status: str = "pending"
    template_key: Optional[str] = None
    message: str = "Задача поставлена в очередь генерации SQL"


class JobStatusResponse(BaseModel):
    job_id: str
    user_id: str
    question: str
    template_key: Optional[str] = None
    status: str
    sql: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict[str, Any]] = None
