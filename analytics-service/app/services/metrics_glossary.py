"""
Семантический слой: глоссарий бизнес-метрик.
Загрузка из `app/data/metrics_glossary.json`, матчинг по тексту запроса.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "metrics_glossary.json"


@lru_cache(maxsize=1)
def _raw_glossary() -> dict[str, Any]:
    if not _DATA_PATH.is_file():
        return {"version": 1, "entries": []}
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_all_entries() -> list[dict[str, Any]]:
    data = _raw_glossary()
    return list(data.get("entries", []))


def match_entries_for_question(question: str, *, max_terms: int = 14) -> list[dict[str, Any]]:
    """Подобрать релевантные термины по пересечению синонимов и заголовков с текстом."""
    ql = question.lower()
    ql_compact = re.sub(r"\s+", " ", ql).strip()
    scored: list[tuple[float, dict[str, Any]]] = []

    for e in get_all_entries():
        score = 0.0
        title = (e.get("title") or "").lower()
        if title and title in ql_compact:
            score += 4.0
        for syn in e.get("synonyms") or []:
            s = syn.lower().strip()
            if len(s) >= 3 and s in ql:
                score += 3.0 + min(2.0, len(s) / 20)
        cat = (e.get("category") or "").lower()
        if cat and cat in ql:
            score += 0.5
        if score > 0:
            scored.append((score, e))

    scored.sort(key=lambda x: -x[0])
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for _, e in scored:
        eid = e.get("id") or e.get("title")
        if eid in seen:
            continue
        seen.add(str(eid))
        out.append(e)
        if len(out) >= max_terms:
            break
    return out


def format_glossary_for_llm(matches: list[dict[str, Any]]) -> str:
    """Текст блока для пользовательского промпта к LLM."""
    if not matches:
        return ""
    lines: list[str] = [
        "Ниже справочник бизнес-терминов (используй смысл при выборе колонок и фильтров):"
    ]
    for e in matches:
        title = e.get("title") or ""
        df = (e.get("definition") or "").strip()
        hints = (e.get("sql_hints") or "").strip()
        syn = ", ".join(e.get("synonyms") or [])[:200]
        chunk = f"- {title}"
        if syn:
            chunk += f" [синонимы: {syn}]"
        if df:
            chunk += f"\n  {df}"
        if hints:
            chunk += f"\n  Подсказка SQL: {hints}"
        lines.append(chunk)
    return "\n".join(lines)


def public_match_models(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Урезанные объекты для API / WS (без огромных полей)."""
    out: list[dict[str, Any]] = []
    for e in matches:
        tid = e.get("id") or e.get("title") or "term"
        out.append(
            {
                "id": str(tid),
                "title": e.get("title"),
                "category": e.get("category"),
                "definition": (e.get("definition") or "")[:600],
            }
        )
    return out
