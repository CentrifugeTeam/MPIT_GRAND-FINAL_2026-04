"""Один batched LLM-вызов: 5 шаблонов (title + instruction) под типы расписания."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas.analytics import TableSchema


SCHEDULE_ORDER = ("once", "daily", "weekly", "monthly", "yearly")


def default_schedules_iso() -> list[dict[str, Any]]:
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    return [
        {"schedule_type": "once", "timezone": "UTC", "once_at": tomorrow.isoformat()},
        {"schedule_type": "daily", "timezone": "UTC", "daily_time": "09:00"},
        {"schedule_type": "weekly", "timezone": "UTC", "weekly_day": 1, "weekly_time": "09:00"},
        {"schedule_type": "monthly", "timezone": "UTC", "monthly_day": 1, "monthly_time": "10:00"},
        {"schedule_type": "yearly", "timezone": "UTC", "yearly_date_ddmm": "01:01", "yearly_time": "10:00"},
    ]


def _schema_digest(tables: list[TableSchema], max_tables: int = 40, max_cols: int = 12) -> str:
    lines: list[str] = []
    for t in tables[:max_tables]:
        cols = ", ".join(f"{c.name}:{c.data_type}" for c in t.columns[:max_cols])
        if len(t.columns) > max_cols:
            cols += ", …"
        lines.append(f"- {t.name}: {cols}")
    return "\n".join(lines) if lines else "(нет таблиц в public)"


def _fallback_templates(source_key: str, display_name: str) -> list[dict[str, str]]:
    base = display_name or source_key
    labels = {
        "once": ("Разовый обзор", f"Краткий разовый отчёт по источнику «{base}»: ключевые метрики и последние изменения."),
        "daily": ("Ежедневная сводка", f"Ежедневная сводка по «{base}»: динамика за последние сутки, сравнение с предыдущим днём."),
        "weekly": ("Недельный отчёт", f"Недельный отчёт по «{base}»: тренды, топ сущностей, отклонения от нормы."),
        "monthly": ("Месячный обзор", f"Месячный обзор по «{base}»: итоги периода, структура, рекомендации."),
        "yearly": ("Годовой отчёт", f"Годовой отчёт по «{base}»: сравнение с прошлым годом, выводы."),
    }
    return [{"title": labels[k][0], "instruction": labels[k][1]} for k in SCHEDULE_ORDER]


async def generate_five_template_texts(
    *,
    source_key: str,
    display_name: str,
    tables: list[TableSchema],
) -> list[dict[str, str]]:
    """Возвращает 5 dict с ключами title, instruction (порядок как SCHEDULE_ORDER)."""
    s = get_settings()
    digest = _schema_digest(tables)
    if not s.LLM_API_KEY:
        return _fallback_templates(source_key, display_name)

    user = (
        f"Источник данных (ключ): {source_key}\n"
        f"Отображаемое имя: {display_name or source_key}\n\n"
        "Фрагмент схемы БД (public):\n"
        f"{digest}\n\n"
        "Сгенерируй ровно 5 объектов JSON-массива в порядке: once, daily, weekly, monthly, yearly.\n"
        "Каждый объект: {\"title\":\"…\",\"instruction\":\"…\"}.\n"
        "title — короткий заголовок шаблона отчёта на русском.\n"
        "instruction — текст запроса аналитику/LLM на русском (1–4 предложения), с учётом реальных таблиц; "
        "без SQL; укажи период анализа в тексте согласно типу (раз / день / неделя / месяц / год).\n"
        "Ответь ТОЛЬКО JSON-массивом без markdown."
    )
    url = s.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {s.LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": s.LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты помощник аналитической платформы. Только JSON-массив из 5 объектов.",
            },
            {"role": "user", "content": user},
        ],
        "temperature": 0.35,
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
    except Exception:
        return _fallback_templates(source_key, display_name)
    if not isinstance(arr, list) or len(arr) < 5:
        return _fallback_templates(source_key, display_name)
    out: list[dict[str, str]] = []
    for i, st in enumerate(SCHEDULE_ORDER):
        item = arr[i] if i < len(arr) else {}
        if not isinstance(item, dict):
            item = {}
        title = str(item.get("title") or "").strip() or _fallback_templates(source_key, display_name)[i]["title"]
        instr = str(item.get("instruction") or "").strip() or _fallback_templates(source_key, display_name)[i][
            "instruction"
        ]
        out.append({"title": title[:500], "instruction": instr[:8000]})
    return out


def build_bulk_templates_payload(
    source_key: str,
    texts: list[dict[str, str]],
    schedules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    sch = schedules or default_schedules_iso()
    templates = []
    for i, sc in enumerate(sch):
        t = texts[i] if i < len(texts) else {"title": "Отчёт", "instruction": "Сводка по данным."}
        templates.append(
            {
                "title": t["title"],
                "instruction": t["instruction"],
                "analytics_source_key": source_key,
                "schedule": sc,
            }
        )
    return {"templates": templates}
