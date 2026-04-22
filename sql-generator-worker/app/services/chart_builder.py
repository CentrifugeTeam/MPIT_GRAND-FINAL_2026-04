import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from app.schemas.analytics import ChartSpec


def _is_numeric(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, (int, float, Decimal)):
        return True
    if isinstance(v, bool):
        return False
    if isinstance(v, str):
        try:
            float(v.replace(",", "."))
            return True
        except ValueError:
            return False
    return False


def _is_temporal_key(name: str, sample: Any) -> bool:
    if isinstance(sample, (datetime, date)):
        return True
    if isinstance(sample, str):
        if re.match(r"^\d{4}-\d{2}-\d{2}", sample):
            return True
        if re.match(r"^\d{4}-\d{2}$", sample):
            return True
    low = name.lower()
    return any(
        x in low
        for x in (
            "date",
            "month",
            "year",
            "day",
            "week",
            "period",
            "time",
            "created",
        )
    )


def build_chart(
    columns: list[str], rows: list[dict[str, Any]]
) -> tuple[ChartSpec, dict[str, Any]]:
    """
    Эвристика: первая подходящая колонка — ось X (категория/время),
    числовые остальные — серии. Иначе только таблица.
    """
    if not rows or not columns:
        spec = ChartSpec(type="table", x_key=None, series=[])
        return spec, {"type": "table", "rows": rows, "columns": columns}

    first_row = rows[0]
    x_key: str | None = None
    for col in columns:
        val = first_row.get(col)
        if not _is_numeric(val):
            x_key = col
            break
    if x_key is None:
        x_key = columns[0]

    numeric_cols: list[str] = []
    for col in columns:
        if col == x_key:
            continue
        v = first_row.get(col)
        if _is_numeric(v):
            numeric_cols.append(col)

    if not numeric_cols or len(rows) > 500:
        spec = ChartSpec(type="table", x_key=x_key, series=[])
        return spec, {
            "type": "table",
            "xKey": x_key,
            "rows": rows,
            "columns": columns,
        }

    chart_type: Literal["line", "bar"] = (
        "line" if _is_temporal_key(x_key, first_row.get(x_key)) else "bar"
    )
    series = [{"key": c, "label": c} for c in numeric_cols]

    labels: list[Any] = [r.get(x_key) for r in rows]
    datasets: list[dict[str, Any]] = []
    for c in numeric_cols:
        datasets.append(
            {
                "key": c,
                "label": c,
                "data": [r.get(c) for r in rows],
            }
        )

    spec = ChartSpec(type=chart_type, x_key=x_key, series=series)
    payload = {
        "type": chart_type,
        "xKey": x_key,
        "labels": labels,
        "series": datasets,
        "rows": rows,
        "columns": columns,
    }
    return spec, payload
