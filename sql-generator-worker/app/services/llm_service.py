import json
import re
from typing import Optional

import httpx

from app.core.config import get_settings
from app.schemas.analytics import ColumnInfo, TableSchema

SYSTEM_PROMPT = """Ты генерируешь только PostgreSQL для аналитики.
Правила:
- Только один запрос: SELECT или WITH ... SELECT. Никаких INSERT/UPDATE/DELETE/DDL.
- Используй только перечисленные таблицы и колонки из схемы (не выдумывай колонку id, если в схеме её нет).
- Фильтры по периоду, кварталу (Q1–Q4), году или дате допускай только через колонки, которые реально есть в схеме для этой таблицы и имеют тип даты/времени (например EXTRACT(QUARTER FROM users.created_at) только если в схеме есть users.created_at). Не добавляй полей «год», «квартал», «период», если их нет среди колонок таблицы. Если подходящей колонки даты нет — не придумывай её; ответь без временного фильтра или ограничься полями из схемы (например только роль).
- Таблица users: первичный ключ — uuid (тип uuid), колонки id нет. JOIN с notification_settings: users.uuid = notification_settings.user_id.
- Таблица nl_sql_jobs: колонка user_id имеет тип uuid (как users.uuid); JOIN делай как u.uuid = nl.user_id без смешения с varchar.
- Если для колонки в схеме перечислены значения enum, используй только эти литералы с тем же регистром (например 'ADMIN', не 'admin'). Не добавляй ролей или значений, которых нет в схеме.
- Если в вопросе встречается значение, которого нет в enum (например "Шрек" для users.role), не подставляй его в SQL как фильтр по enum-колонке.
- Не добавляй лишние JOIN к другим таблицам, если они не нужны для ответа на вопрос (избегай произвольного JOIN «на всякий случай»).
- Пиши корректный PostgreSQL (даты, агрегаты, фильтры, GROUP BY по необходимости).
- Не добавляй пояснений до и после SQL. Выведи один блок ```sql ... ``` с финальным запросом.
"""


def _column_prompt(c: ColumnInfo) -> str:
    if c.enum_values:
        vals = ", ".join(f"'{v}'" for v in c.enum_values)
        return f"{c.name} ({c.data_type}, enum: {vals})"
    return f"{c.name} ({c.data_type})"


def _schema_to_prompt(tables: list[TableSchema]) -> str:
    lines: list[str] = ["Схема базы (public):"]
    for t in tables:
        cols = ", ".join(_column_prompt(c) for c in t.columns)
        lines.append(f"- {t.name}: {cols}")
    return "\n".join(lines)


def _extract_sql(text: str) -> str:
    text = text.strip()
    m = re.search(r"```(?:sql)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _extract_explanation(text: str) -> Optional[str]:
    # Удаляем блок sql, остальное считаем кратким пояснением (если короткое)
    stripped = re.sub(r"```(?:sql)?\s*[\s\S]*?```", "", text, flags=re.IGNORECASE).strip()
    if not stripped or len(stripped) > 2000:
        return None
    return stripped or None


async def generate_sql(
    question: str,
    tables: list[TableSchema],
    glossary_context: Optional[str] = None,
    orchestrator_hints: Optional[str] = None,
) -> tuple[str, Optional[str], str]:
    """
    Возвращает (sql, explanation, raw_response_excerpt).
    """
    settings = get_settings()
    if not settings.LLM_API_KEY:
        raise ValueError(
            "LLM_API_KEY не задан: укажите ключ в переменных окружения сервиса analytics"
        )

    user_content = (
        _schema_to_prompt(tables)
        + "\n\nВопрос пользователя:\n"
        + question.strip()
    )
    if glossary_context and glossary_context.strip():
        user_content += "\n\n" + glossary_context.strip()
    if orchestrator_hints and orchestrator_hints.strip():
        user_content += (
            "\n\nПодсказки аналитика по схеме (учти при генерации SQL):\n"
            + orchestrator_hints.strip()
        )

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
    }

    url = settings.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected LLM response: {json.dumps(data)[:800]}") from e

    sql = _extract_sql(content)
    if not sql:
        raise ValueError("Модель не вернула SQL")

    excerpt = content[:1200] if len(content) > 1200 else content
    return sql, _extract_explanation(content), excerpt
