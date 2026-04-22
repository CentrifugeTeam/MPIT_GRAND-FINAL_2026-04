"""Row-level data access: role + source_key → allowed tables / denied columns (deny if no policy, non-ADMIN)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class AccessPolicyView:
    """Resolved policy for NL / schema filtering."""

    allowed_tables_lower: frozenset[str]  # empty = deny all; {"*"} = all tables
    denied_columns: dict[str, frozenset[str]]  # table_lower -> cols; key "*" = all tables

    def table_allowed(self, table_name: str) -> bool:
        t = table_name.strip().lower()
        if not self.allowed_tables_lower:
            return False
        if "*" in self.allowed_tables_lower:
            return True
        return t in self.allowed_tables_lower

    def column_allowed(self, table_name: str, column_name: str) -> bool:
        if not self.table_allowed(table_name):
            return False
        c = column_name.strip().lower()
        t = table_name.strip().lower()
        for scope, cols in self.denied_columns.items():
            if scope == "*" or scope == t:
                if c in cols:
                    return False
        return True


def _norm_set(v: Any) -> frozenset[str]:
    if v is None:
        return frozenset()
    if isinstance(v, list):
        return frozenset(str(x).strip().lower() for x in v if str(x).strip())
    return frozenset()


def _norm_denied(v: Any) -> dict[str, frozenset[str]]:
    out: dict[str, frozenset[str]] = {}
    if not isinstance(v, dict):
        return out
    for k, cols in v.items():
        key = str(k).strip().lower()
        if isinstance(cols, list):
            out[key] = frozenset(str(c).strip().lower() for c in cols if str(c).strip())
    return out


def policy_view_from_row(allowed_tables: Any, denied_columns: Any) -> AccessPolicyView:
    at = _norm_set(allowed_tables)
    dc = _norm_denied(denied_columns)
    return AccessPolicyView(allowed_tables_lower=at, denied_columns=dc)


def filter_schema_tables(
    tables: list[dict[str, Any]],
    policy: AccessPolicyView,
) -> list[dict[str, Any]]:
    """Return shallow-copied table dicts with columns filtered by policy."""
    out: list[dict[str, Any]] = []
    for t in tables:
        name = str(t.get("name") or "").strip()
        if not name or not policy.table_allowed(name):
            continue
        cols_in = t.get("columns") or []
        cols_out: list[dict[str, Any]] = []
        for c in cols_in:
            if isinstance(c, dict):
                cn = str(c.get("name") or "")
            else:
                cn = str(getattr(c, "name", "") or "")
            if cn and policy.column_allowed(name, cn):
                cols_out.append(dict(c) if isinstance(c, dict) else c)
        row = dict(t)
        row["columns"] = cols_out
        out.append(row)
    return out


def admin_bypass(role: Optional[str]) -> bool:
    return (role or "").strip().upper() == "ADMIN"
