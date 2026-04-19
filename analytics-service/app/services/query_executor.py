from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine


def execute_select(engine: Engine, sql: str, timeout_ms: int) -> tuple[list[str], list[dict[str, Any]]]:
    stmt = text(sql).execution_options(autocommit=False)
    with engine.connect() as conn:
        conn.execute(text(f"SET LOCAL statement_timeout = {int(timeout_ms)}"))
        result = conn.execute(stmt)
        cols = list(result.keys())
        rows_raw = result.fetchall()
    rows: list[dict[str, Any]] = []
    for tup in rows_raw:
        row = {}
        for i, col in enumerate(cols):
            val = tup[i]
            # JSON-сериализуемые типы для ответа API
            if hasattr(val, "isoformat"):
                row[col] = val.isoformat()
            else:
                row[col] = val
        rows.append(row)
    return cols, rows
