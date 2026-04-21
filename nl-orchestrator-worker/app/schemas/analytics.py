from typing import Optional

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    enum_values: Optional[list[str]] = None


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnInfo]
