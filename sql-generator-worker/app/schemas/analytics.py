from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    enum_values: Optional[list[str]] = None


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnInfo]


class ChartSpec(BaseModel):
    type: Literal["line", "bar", "table"] = "table"
    x_key: Optional[str] = None
    series: list[dict[str, str]] = Field(default_factory=list)
