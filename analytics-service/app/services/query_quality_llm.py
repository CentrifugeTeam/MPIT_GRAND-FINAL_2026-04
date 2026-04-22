"""LLM-only review of NL question / optional SQL — no execution."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings


async def analyze_query_quality(
    *,
    question: str,
    sql: str | None = None,
    interpretation_warnings: list[str] | None = None,
) -> dict[str, Any]:
    s = get_settings()
    if not s.LLM_API_KEY:
        return {
            "summary": "LLM не настроен (нет LLM_API_KEY).",
            "risks": [],
            "suggested_questions": [],
            "suggested_sql_hints": "",
        }
    warn = "\n".join(interpretation_warnings or []) or "(нет)"
    sql_part = f"\nSQL (черновик, не выполнять):\n{sql}\n" if sql and sql.strip() else ""
    user = (
        f"Вопрос пользователя:\n{question}\n\n"
        f"Предупреждения эвристического разбора:\n{warn}\n"
        f"{sql_part}\n"
        "Оцени полноту и риск неверной интерпретации. Ответь ТОЛЬКО JSON:\n"
        '{"summary":"","risks":[],"suggested_questions":[],"suggested_sql_hints":""}\n'
        "suggested_questions: 1–3 коротких уточняющих вопроса пользователю по-русски или []."
    )
    url = s.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {s.LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": s.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты помощник аналитика. Не выполняй SQL. Только JSON без markdown.",
            },
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    raw = str(data["choices"][0]["message"]["content"])
    m = re.search(r"\{[\s\S]*\}\s*$", raw.strip())
    if m:
        raw = m.group(0)
    try:
        out = json.loads(raw)
    except Exception:
        return {
            "summary": raw[:500],
            "risks": [],
            "suggested_questions": [],
            "suggested_sql_hints": "",
        }
    return {
        "summary": str(out.get("summary") or "")[:2000],
        "risks": list(out.get("risks") or [])[:20],
        "suggested_questions": list(out.get("suggested_questions") or [])[:5],
        "suggested_sql_hints": str(out.get("suggested_sql_hints") or "")[:2000],
    }
