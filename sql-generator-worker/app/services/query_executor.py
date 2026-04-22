import json
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


def explain_total_cost(engine: Engine, sql: str, timeout_ms: int) -> Optional[float]:
    """Return planner Total Cost from EXPLAIN (FORMAT JSON) or None on failure."""
    stmt = text(f"EXPLAIN (FORMAT JSON) {sql}").execution_options(autocommit=False)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET LOCAL statement_timeout = {int(timeout_ms)}"))
            row = conn.execute(stmt).fetchone()
    except Exception:
        return None
    if not row or not row[0]:
        return None
    try:
        payload = row[0]
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        if isinstance(data, list) and data and isinstance(data[0], dict):
            plan = data[0].get("Plan")
            if isinstance(plan, dict) and "Total Cost" in plan:
                return float(plan["Total Cost"])
    except Exception:
        return None
    return None


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
