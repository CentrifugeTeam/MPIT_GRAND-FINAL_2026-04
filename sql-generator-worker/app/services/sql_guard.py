import re
from typing import Any, Optional, Sequence, Set, Tuple

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


def _schema_meta(
    schema_tables: Optional[Sequence[Any]],
) -> Optional[dict[str, dict[str, Any]]]:
    if not schema_tables:
        return None
    out: dict[str, dict[str, Any]] = {}
    for t in schema_tables:
        if hasattr(t, "name"):
            name = str(t.name).lower()
            cols_attr = getattr(t, "columns", None) or []
        elif isinstance(t, dict):
            name = str(t["name"]).lower()
            cols_attr = t.get("columns") or []
        else:
            continue
        col_names: Set[str] = set()
        enum_map: dict[str, Set[str]] = {}
        for c in cols_attr:
            if hasattr(c, "name"):
                cname = str(c.name).lower()
                col_names.add(cname)
                values = getattr(c, "enum_values", None)
                if values:
                    enum_map[cname] = {str(v) for v in values}
            elif isinstance(c, dict):
                cname = str(c["name"]).lower()
                col_names.add(cname)
                values = c.get("enum_values")
                if values:
                    enum_map[cname] = {str(v) for v in values}
        out[name] = {"columns": col_names, "enums": enum_map}
    return out or None


def _physical_alias_map(
    root: exp.Expression, meta: dict[str, dict[str, Any]]
) -> dict[str, str]:
    """Maps table name / alias → physical public table name (only known schema tables)."""
    m: dict[str, str] = {}
    for t in root.find_all(exp.Table):
        base = (t.name or "").lower()
        if not base or base not in meta:
            continue
        m[base] = base
        al = t.args.get("alias")
        if isinstance(al, exp.TableAlias) and al.name:
            m[str(al.name).lower()] = base
    return m


def _schema_column_errors(
    root: exp.Expression, meta: dict[str, dict[str, Any]]
) -> list[str]:
    alias_map = _physical_alias_map(root, meta)
    if not alias_map:
        return []
    physical_used = set(alias_map.values())
    errors: list[str] = []
    for col in root.find_all(exp.Column):
        cname_raw = col.name
        if not cname_raw:
            continue
        cname = str(cname_raw).lower()
        tbl_raw = col.table
        tbl = str(tbl_raw).lower() if tbl_raw else ""
        if tbl:
            base = alias_map.get(tbl, tbl)
            if base not in meta:
                continue
            if cname not in meta[base]["columns"]:
                errors.append(
                    f"Колонка «{tbl_raw}.{cname_raw}» отсутствует в таблице «{base}» по схеме БД"
                )
            continue
        candidates = [b for b in physical_used if cname in meta.get(b, {}).get("columns", set())]
        if len(candidates) == 0:
            errors.append(
                f"Колонка «{cname_raw}» не найдена ни в одной из используемых таблиц схемы "
                f"({', '.join(sorted(physical_used))})"
            )
        elif len(candidates) > 1:
            errors.append(
                f"Колонка «{cname_raw}» неоднозначна (есть в: {', '.join(sorted(candidates))}); "
                "укажите таблицу или алиас"
            )
    return errors


def _literal_values_from_expr(node: exp.Expression) -> Optional[Set[str]]:
    if isinstance(node, exp.Literal):
        if node.is_string:
            return {node.this}
        return {str(node.this)}
    if isinstance(node, exp.Tuple):
        vals: Set[str] = set()
        for x in node.expressions:
            if not isinstance(x, exp.Literal):
                return None
            vals.add(x.this if x.is_string else str(x.this))
        return vals
    return None


def _resolve_column_base(
    col: exp.Column,
    alias_map: dict[str, str],
    meta: dict[str, dict[str, Any]],
) -> Optional[tuple[str, str]]:
    cname_raw = col.name
    if not cname_raw:
        return None
    cname = str(cname_raw).lower()
    tbl_raw = col.table
    tbl = str(tbl_raw).lower() if tbl_raw else ""
    if tbl:
        base = alias_map.get(tbl, tbl)
        if base in meta and cname in meta[base]["columns"]:
            return base, cname
        return None
    candidates = [b for b in set(alias_map.values()) if cname in meta.get(b, {}).get("columns", set())]
    if len(candidates) == 1:
        return candidates[0], cname
    return None


def _schema_enum_errors(
    root: exp.Expression, meta: dict[str, dict[str, Any]]
) -> list[str]:
    alias_map = _physical_alias_map(root, meta)
    if not alias_map:
        return []
    errors: list[str] = []
    compare_nodes: tuple[type[exp.Expression], ...] = (
        exp.EQ,
        exp.NEQ,
        exp.In,
    )
    for node in root.walk():
        if not isinstance(node, compare_nodes):
            continue
        left = node.args.get("this")
        right = node.args.get("expression")
        if isinstance(node, exp.In):
            right = node.args.get("expressions")
            if right is not None:
                right = exp.Tuple(expressions=right)
        if isinstance(left, exp.Column):
            col_side = left
            val_side = right
        elif isinstance(right, exp.Column):
            col_side = right
            val_side = left
        else:
            continue
        if not isinstance(col_side, exp.Column) or not isinstance(val_side, exp.Expression):
            continue
        resolved = _resolve_column_base(col_side, alias_map, meta)
        if not resolved:
            continue
        base, cname = resolved
        allowed_values = meta[base]["enums"].get(cname)
        if not allowed_values:
            continue
        used_values = _literal_values_from_expr(val_side)
        if not used_values:
            continue
        bad = sorted(v for v in used_values if v not in allowed_values)
        if bad:
            errors.append(
                f"Недопустимое enum-значение для «{base}.{cname}»: {', '.join(bad)}. "
                f"Допустимо: {', '.join(sorted(allowed_values))}"
            )
    return errors


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


def _count_union_nodes(node: exp.Expression) -> int:
    n = 0
    for x in node.walk():
        if isinstance(x, exp.Union):
            n += 1
    return n


def _parse_access_policy(raw: Any) -> tuple[Optional[Set[str]], dict[str, Set[str]]]:
    """Returns (allowed_tables or None if wildcard, denied map table->set of cols)."""
    if not isinstance(raw, dict):
        return None, {}
    at = raw.get("allowed_tables")
    allowed: Optional[Set[str]] = None
    if isinstance(at, list) and at:
        s = {str(x).strip().lower() for x in at if str(x).strip()}
        if "*" in s:
            allowed = None
        else:
            allowed = s
    dc_in = raw.get("denied_columns") or {}
    denied: dict[str, Set[str]] = {}
    if isinstance(dc_in, dict):
        for k, v in dc_in.items():
            key = str(k).strip().lower()
            if isinstance(v, list):
                denied[key] = {str(c).strip().lower() for c in v if str(c).strip()}
    return allowed, denied


def _root_select_has_star(node: exp.Expression) -> bool:
    root = node
    if isinstance(node, exp.With) and node.this:
        root = node.this
    if not isinstance(root, exp.Select):
        return False
    for sel in root.find_all(exp.Select):
        for ex in sel.expressions:
            if isinstance(ex, exp.Star) or (isinstance(ex, exp.Column) and ex.name == "*"):
                return True
    return False


def _enforce_access_policy(
    node: exp.Expression,
    physical_tables: Set[str],
    access_policy: Optional[dict[str, Any]],
) -> None:
    if not access_policy:
        return
    pol_allow, denied = _parse_access_policy(access_policy)
    if pol_allow is not None and physical_tables:
        extra = physical_tables - pol_allow
        if extra:
            raise ValueError(
                f"Таблицы вне политики доступа: {', '.join(sorted(extra))}"
            )
    if denied and physical_tables:
        star = _root_select_has_star(node)
        if star:
            for t in physical_tables:
                banned = set(denied.get(t, set())) | set(denied.get("*", set()))
                if banned:
                    raise ValueError(
                        "SELECT * запрещён: для используемых таблиц заданы запрещённые колонки; "
                        "перечислите колонки явно."
                    )
        for col in node.find_all(exp.Column):
            cname = (col.name or "").lower()
            if not cname:
                continue
            tbl_raw = col.table
            if tbl_raw:
                base = str(tbl_raw).lower()
                if base in physical_tables:
                    banned = denied.get(base, set()) | denied.get("*", set())
                    if cname in banned:
                        raise ValueError(f"Колонка «{base}.{cname}» запрещена политикой доступа")


def validate_and_prepare_sql(
    raw_sql: str,
    max_rows: Optional[int],
    allowed: Optional[Set[str]],
    schema_tables: Optional[Sequence[Any]] = None,
    access_policy: Optional[dict[str, Any]] = None,
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

    if _count_union_nodes(node) > 8:
        raise ValueError("Слишком много UNION; упростите запрос")

    names = _table_names(node)
    _enforce_access_policy(node, names, access_policy)

    if allowed is not None and names:
        extra = names - allowed
        if extra:
            raise ValueError(
                f"Таблицы вне разрешённого списка: {', '.join(sorted(extra))}"
            )

    s = get_settings()
    if len(one.encode("utf-8")) > int(getattr(s, "MAX_SQL_TEXT_BYTES", 256_000) or 256_000):
        raise ValueError("SQL слишком длинный")

    meta = _schema_meta(schema_tables)
    if meta:
        col_err = _schema_column_errors(node, meta)
        if col_err:
            raise ValueError("; ".join(col_err))
        enum_err = _schema_enum_errors(node, meta)
        if enum_err:
            raise ValueError("; ".join(enum_err))

    final_node = node
    if max_rows is not None:
        final_node = _apply_limit(node, max_rows)
        warnings.append(
            f"При необходимости добавлен LIMIT не более {max_rows} строк"
        )
    out = final_node.sql(dialect="postgres")
    if not out or not out.strip():
        raise ValueError("Не удалось сгенерировать SQL")

    return out, warnings
