from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas.analytics import TableSchema
from app.services.chat_suggestions_store import MAX_TOPICS, QUESTIONS_PER_TOPIC


def _schema_digest(tables: list[TableSchema], max_tables: int = 40, max_cols: int = 12) -> str:
    lines: list[str] = []
    for t in tables[:max_tables]:
        cols = ", ".join(f"{c.name}:{c.data_type}" for c in t.columns[:max_cols])
        if len(t.columns) > max_cols:
            cols += ", ..."
        lines.append(f"- {t.name}: {cols}")
    return "\n".join(lines) if lines else "(нет таблиц в public)"


def _fallback_topics(display_name: str) -> list[dict[str, Any]]:
    base = display_name.strip() or "источника"
    return [
        {
            "topic_key": "users",
            "topic_label": "Пользовательская аналитика",
            "questions": [
                f"Сколько уникальных пользователей в {base} за текущий месяц?",
                f"Как менялось число активных пользователей в {base} по неделям?",
                f"Какие сегменты пользователей в {base} растут быстрее всего?",
                f"Какой отток пользователей в {base} за последние 30 дней?",
            ],
        },
        {
            "topic_key": "sales",
            "topic_label": "Продажи и выручка",
            "questions": [
                f"Какая выручка в {base} по месяцам за текущий год?",
                f"Какие товары или категории дают наибольшую выручку в {base}?",
                f"Как меняется средний чек в {base} по неделям?",
                f"Какие регионы дают лучший вклад в выручку в {base}?",
            ],
        },
        {
            "topic_key": "operations",
            "topic_label": "Операционные метрики",
            "questions": [
                f"Какие процессы в {base} имеют наибольшее время выполнения?",
                f"Где в {base} больше всего отмен или ошибок за последний месяц?",
                f"Как меняется нагрузка по дням недели в {base}?",
                f"Какие аномалии в операционных метриках видны в {base} за 14 дней?",
            ],
        },
    ]


def normalize_topics(raw_topics: list[dict[str, Any]], fallback_display_name: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen_topics: set[str] = set()
    for t in raw_topics:
        label = str(t.get("topic_label") or "").strip()
        topic_key = str(t.get("topic_key") or label).strip().lower()
        if not label or not topic_key or topic_key in seen_topics:
            continue
        qs_raw = t.get("questions")
        if not isinstance(qs_raw, list):
            continue
        uniq: list[str] = []
        seen_q: set[str] = set()
        for q in qs_raw:
            v = str(q or "").strip()
            if not v:
                continue
            lk = v.lower()
            if lk in seen_q:
                continue
            seen_q.add(lk)
            uniq.append(v)
            if len(uniq) >= QUESTIONS_PER_TOPIC:
                break
        if len(uniq) < QUESTIONS_PER_TOPIC:
            continue
        out.append({"topic_key": topic_key[:64], "topic_label": label[:255], "questions": uniq[:QUESTIONS_PER_TOPIC]})
        seen_topics.add(topic_key)
        if len(out) >= MAX_TOPICS:
            break
    if out:
        return out
    return _fallback_topics(fallback_display_name)


async def generate_chat_suggestion_topics(
    *,
    source_key: str,
    display_name: str,
    tables: list[TableSchema],
    locale: str = "ru",
) -> list[dict[str, Any]]:
    s = get_settings()
    if locale.strip().lower() != "ru":
        return _fallback_topics(display_name)
    if not s.LLM_API_KEY:
        return _fallback_topics(display_name)
    digest = _schema_digest(tables)
    prompt = (
        f"Источник данных: {source_key}\n"
        f"Отображаемое имя: {display_name or source_key}\n\n"
        "Фрагмент схемы БД:\n"
        f"{digest}\n\n"
        "Сформируй FAQ-подсказки для аналитического чата на русском языке.\n"
        f"Нужно не больше {MAX_TOPICS} тем.\n"
        f"В каждой теме ровно {QUESTIONS_PER_TOPIC} вопроса.\n"
        "Верни ТОЛЬКО JSON-массив topics: "
        '[{"topic_key":"...","topic_label":"...","questions":["...","...","...","..."]}]'
    )
    url = s.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {s.LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": s.LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Ты генерируешь только JSON-массив тем FAQ без markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    raw = str(data["choices"][0]["message"]["content"])
    m = re.search(r"\[[\s\S]*\]\s*$", raw.strip())
    if m:
        raw = m.group(0)
    try:
        arr = json.loads(raw)
        if not isinstance(arr, list):
            return _fallback_topics(display_name)
    except Exception:
        return _fallback_topics(display_name)
    casted = [x for x in arr if isinstance(x, dict)]
    return normalize_topics(casted, fallback_display_name=display_name or source_key)
