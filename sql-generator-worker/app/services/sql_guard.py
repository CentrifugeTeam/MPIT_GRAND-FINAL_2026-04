import re
from typing import Optional, Set, Tuple

import sqlglot
from sqlglot import exp

from app.core.config import get_settings

_FORBIDDEN_ROOT = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.AlterTable,
    exp.TruncateTable,
    exp.Command,
    exp.Merge,
)

_DANGEROUS_FUNCS = frozenset(
    {
        "pg_sleep",
        "dblink",
        "dblink_connect",
        "lo_import",
        "lo_export",
    }
)


def _extract_sql_from_markdown(text: str) -> str:
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _parse_postgres(sql: str) -> exp.Expression:
    return sqlglot.parse_one(sql, read="postgres")


def _forbidden_expressions(node: exp.Expression) -> list[str]:
    found: list[str] = []
    for n in node.walk():
        for cls in _FORBIDDEN_ROOT:
            if isinstance(n, cls):
                found.append(f"forbidden: {type(n).__name__}")
    for n in node.find_all(exp.Anonymous):
        if n.name and n.name.lower() in _DANGEROUS_FUNCS:
            found.append(f"forbidden function: {n.name}")
    return found


def _root_is_readonly_select(node: exp.Expression) -> bool:
    if isinstance(node, (exp.Select, exp.Union, exp.Except, exp.Intersect)):
        return True
    if isinstance(node, exp.Subquery):
        return _root_is_readonly_select(node.this)
    if isinstance(node, exp.With) and node.this:
        return _root_is_readonly_select(node.this)
    return False


def _table_names(node: exp.Expression) -> Set[str]:
    names: Set[str] = set()
    for t in node.find_all(exp.Table):
        n = t.name
        if n:
            names.add(n.lower())
    return names


def _apply_limit(node: exp.Expression, max_rows: int) -> exp.Expression:
    if isinstance(node, exp.With):
        inner = node.this
        new_inner = _apply_limit(inner, max_rows)
        out = node.copy()
        out.set("this", new_inner)
        return out
    if isinstance(node, exp.Select):
        if node.args.get("limit") is None:
            return node.limit(max_rows)
        return node
    if isinstance(node, exp.Union):
        if node.args.get("limit") is None:
            return node.limit(max_rows)
        return node
    return node


def allowed_table_set() -> Optional[Set[str]]:
    raw = get_settings().ALLOWED_TABLES
    if not raw or not raw.strip():
        return None
    return {t.strip().lower() for t in raw.split(",") if t.strip()}


def validate_and_prepare_sql(
    raw_sql: str, max_rows: int, allowed: Optional[Set[str]]
) -> Tuple[str, list[str]]:
    warnings: list[str] = []
    sql = _extract_sql_from_markdown(raw_sql)
    if not sql or not sql.strip():
        raise ValueError("Пустой SQL")

    one = sql.rstrip().rstrip(";")
    if ";" in one:
        raise ValueError("Разрешён только один SQL-запрос")

    try:
        node = _parse_postgres(one)
    except Exception as e:
        raise ValueError(f"SQL parse error: {e}") from e

    if not _root_is_readonly_select(node):
        raise ValueError("Разрешены только SELECT (включая WITH ... SELECT)")

    bad = _forbidden_expressions(node)
    if bad:
        raise ValueError("; ".join(bad))

    names = _table_names(node)
    if allowed is not None and names:
        extra = names - allowed
        if extra:
            raise ValueError(
                f"Таблицы вне разрешённого списка: {', '.join(sorted(extra))}"
            )

    limited = _apply_limit(node, max_rows)
    out = limited.sql(dialect="postgres")
    if not out or not out.strip():
        raise ValueError("Не удалось сгенерировать SQL")

    warnings.append(f"Применён LIMIT не более {max_rows} строк")
    return out, warnings


def preview_strip(raw: str) -> str:
    return _extract_sql_from_markdown(raw)
