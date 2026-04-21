from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings
from app.schemas.analytics import ColumnInfo, TableSchema

logger = logging.getLogger(__name__)

PLAN_SYSTEM = """Ты аналитический ассистент по данным из PostgreSQL. Пользователь пишет на русском.
У тебя есть только перечисленная схема таблиц — не выдумывай колонки и не подставляй значения enum вне списка в схеме.

Схема в этом сообщении — актуальное подключение для ТЕКУЩЕГО шага (пользователь мог сменить базу в интерфейсе).
Если спрашивают: какие таблицы видишь / что за схема / «а сейчас какие таблицы» / перечисли таблицы — отвечай только по блоку «Схема базы» ниже. Не повторяй и не подтверждай ответы ассистента из истории чата про таблицы: они могли относиться к другой БД.

Разговор без нового запроса к данным (обязательно sql_question = null):
- Прощания, благодарности, согласие, междометия: «пока», «пока 2 раза», «спасибо», «ок», «ага», «хорошо», «ладно», «понял», «да/нет» без уточнения метрики — ответь по-человечески коротко, НЕ повторяй цифры и выводы из предыдущих сообщений в чате, НЕ делай новый SQL.
- Если в сообщении нет явного нового аналитического вопроса (что посчитать, по какой таблице, за какой период) — не ставь sql_question, даже если в истории недавно обсуждали выборку.
- Шутки, «проверка связи», случайный набор букв без смысла запроса к БД — sql_question = null, reply_ru кратко.

Реши:
- Если для ответа нужны данные из БД — заполни поле sql_question одной строкой: формулировка на естественном языке для сервиса генерации SQL (как отдельный аналитический запрос).
- Если достаточно пояснить без запроса к БД — sql_question = null, а reply_ru — ответ пользователю.
- Если пользователь просит «все данные», «всю таблицу», «выгрузи все строки», «покажи всё из таблицы …» — это запрос к БД: поставь sql_question с явной формулировкой (например «выбрать все колонки из таблицы X с LIMIT … для предпросмотра»), не отказывай в reply_ru от выполнения запроса и не требуй «переформулировать вопрос», если таблица уже ясна из контекста. Краткий reply_ru можно оставить пустым или одной фразой «Запрашиваю данные».

Графики и визуализация:
- Запрещено предлагать «внешние сервисы», «отдельные библиотеки» или отказывать в графике: после SQL клиент сам строит bar/line из таблицы (категория + числа).
- Если пользователь просит график/диаграмму по данным из БД — почти всегда нужен sql_question с формулировкой, чтобы в результате были колонки вида «категория + число(а)» (например роль и count). Повторный запрос к БД допустим, даже если похожие данные уже обсуждались в истории.
- Если запрос на график неоднозначен (не ясно: по какой метрике, за какой период, какая ось, столбцы vs линия vs круговая) — поставь sql_question = null и в reply_ru задай 1–3 коротких уточняющих вопроса по-русски; не выдумывай SQL.

Поле sql_hints_ru — краткие подсказки для генератора SQL (join, фильтры по датам только если есть колонки дат), или пустая строка.

Ответь ТОЛЬКО JSON без markdown:
{"reply_ru":"","sql_question":null,"sql_hints_ru":""}
"""

# Короткие реплики без запроса к БД (обход LLM, чтобы не дублировать прошлый отчёт).
_CONV_ONE_WORD = frozenset(
    {
        "пока",
        "спасибо",
        "спс",
        "ок",
        "окей",
        "okay",
        "ага",
        "угу",
        "хорошо",
        "ладно",
        "понял",
        "понятно",
        "ясно",
        "да",
        "нет",
        "привет",
        "здравствуй",
        "здравствуйте",
        "добрыйдень",
        "добрыйвечер",
        "досвидания",
        "бай",
        "bye",
        "thanks",
        "thx",
        "спасибо",
        "мерси",
        "норм",
        "нормально",
        "супер",
        "круто",
        "👍",
        "ок.",
    },
)

_CONV_RE = re.compile(
    r"^(пока|спасибо|спс|thx|thanks)(\s+\d+)?(\s+раза?|\s+раз)?$",
    re.IGNORECASE,
)


def _normalized_chat_token(s: str) -> str:
    x = re.sub(r"\s+", "", s.strip().lower())
    return x.rstrip(".!?…")


def _is_obviously_conversational(user_text: str) -> bool:
    raw = user_text.strip()
    if not raw:
        return True
    t = raw.lower()
    compact = _normalized_chat_token(raw)
    if compact in _CONV_ONE_WORD:
        return True
    if _CONV_RE.match(t.strip()):
        return True
    # «пока» с лишними пробелами/знаками
    if re.fullmatch(r"пока[\s!.]*", t, flags=re.IGNORECASE):
        return True
    return False


def _conversational_reply_ru(user_text: str) -> str:
    t = user_text.strip().lower()
    if "спасиб" in t or "thx" in t or "thanks" in t or "мерси" in t:
        return "Пожалуйста! Если понадобится ещё выборка из базы — напишите новый вопрос."
    if "привет" in t or "здравствуй" in t or "добрый" in t:
        return "Здравствуйте! Задайте вопрос по данным в базе — постараюсь помочь."
    if re.search(r"\b(bye|бай|пока|досвидания)\b", t):
        return "До встречи! Когда будете готовы продолжить с данными — напишите."
    if t in ("ок", "ок.", "okay", "окей", "ага", "угу", "хорошо", "ладно", "понял", "понятно", "ясно", "да", "нет"):
        return "Хорошо. Если нужен следующий запрос к базе — формулируйте его целиком."
    return "Ок. Если это был не вопрос к базе — напишите, что именно посчитать или показать."


FINAL_SYSTEM = """Ты аналитик. Пользователь задал вопрос; выполнен SQL; ниже фрагмент результата.
Сформируй JSON без markdown:
{"reply_ru":"короткий ответ по данным","report_ru":"краткий текстовый отчёт: что посчитано, выводы, ограничения выборки"}
Никогда не оставляй оба поля reply_ru и report_ru пустыми: хотя бы одно короткое предложение на русском (даже если строк 0 или данные очевидны из таблицы).
Если SQL завершился ошибкой — объясни в reply_ru и report_ru по-русски, не выдумывай чисел.
Если пользователь просил график и данные подходят (есть категории и числа) — в reply_ru одной фразой укажи, что столбчатый или линейный график показывается в интерфейсе чата; не предлагай внешние инструменты для графиков.
"""


def _column_line(c: ColumnInfo) -> str:
    if c.enum_values:
        vals = ", ".join(f"'{v}'" for v in c.enum_values)
        return f"{c.name} ({c.data_type}, enum: {vals})"
    return f"{c.name} ({c.data_type})"


def schema_block(tables: list[TableSchema]) -> str:
    lines = ["Схема базы (public) — для этого сообщения используй только эти таблицы:"]
    for t in tables:
        cols = ", ".join(_column_line(c) for c in t.columns)
        lines.append(f"- {t.name}: {cols}")
    return "\n".join(lines)


def _parse_json_obj(text: str) -> dict[str, Any]:
    text = text.strip()
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if m:
        text = m.group(0)
    return json.loads(text)


async def _chat(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    s = get_settings()
    if not s.LLM_API_KEY:
        raise ValueError("LLM_API_KEY не задан для nl-orchestrator-worker")
    url = s.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {s.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": s.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected LLM: {json.dumps(data)[:600]}") from e


async def plan_turn(
    user_text: str,
    tables: list[TableSchema],
    history: list[dict[str, str]],
    *,
    active_source_label: Optional[str] = None,
) -> dict[str, Any]:
    if _is_obviously_conversational(user_text):
        return {
            "reply_ru": _conversational_reply_ru(user_text),
            "sql_question": None,
            "sql_hints_ru": "",
        }
    src_note = ""
    if active_source_label and active_source_label.strip():
        src_note = (
            "\n\nАктивный источник данных (используется только эта БД): "
            + active_source_label.strip()
        )
    sys = PLAN_SYSTEM + src_note + "\n\n" + schema_block(tables)
    messages: list[dict[str, str]] = [{"role": "system", "content": sys}]
    lim = max(1, get_settings().CHAT_MAX_HISTORY_MESSAGES)
    for h in history[-lim:]:
        role = h.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        messages.append({"role": role, "content": str(h.get("content", ""))})
    messages.append({"role": "user", "content": user_text})
    raw = await _chat(messages, temperature=0.2)
    try:
        out = _parse_json_obj(raw)
    except Exception as e:
        logger.warning("plan_turn JSON parse failed: %s", e)
        return {"reply_ru": raw[:2000], "sql_question": None, "sql_hints_ru": ""}
    sq = out.get("sql_question")
    sql_q = None
    if isinstance(sq, str) and sq.strip():
        sql_q = sq.strip()
    return {
        "reply_ru": str(out.get("reply_ru") or "").strip(),
        "sql_question": sql_q,
        "sql_hints_ru": str(out.get("sql_hints_ru") or "").strip(),
    }


def _truncate_rows(rows: List[Dict[str, Any]], max_rows: int, max_chars: int) -> str:
    chunk = rows[:max_rows]
    s = json.dumps(chunk, ensure_ascii=False, default=str)
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 24] + "\n…(обрезано)"


async def finalize_after_sql(
    user_text: str,
    sql: Optional[str],
    error: Optional[str],
    columns: list[str],
    rows: List[Dict[str, Any]],
) -> dict[str, str]:
    payload = {
        "user_question": user_text,
        "sql": sql or "",
        "execution_error": error or "",
        "columns": columns,
        "rows_json": _truncate_rows(rows, max_rows=40, max_chars=20000),
    }
    user_content = json.dumps(payload, ensure_ascii=False)
    messages = [
        {"role": "system", "content": FINAL_SYSTEM},
        {"role": "user", "content": user_content},
    ]
    raw = await _chat(messages, temperature=0.3)
    try:
        out = _parse_json_obj(raw)
    except Exception as e:
        logger.warning("finalize JSON parse failed: %s", e)
        return {"reply_ru": raw[:4000], "report_ru": ""}
    reply = str(out.get("reply_ru") or "").strip()
    report = str(out.get("report_ru") or "").strip()
    if reply or report:
        return {"reply_ru": reply, "report_ru": report}
    if error:
        return {
            "reply_ru": f"Ошибка выполнения SQL: {error}",
            "report_ru": "",
        }
    if rows:
        n = len(rows)
        return {
            "reply_ru": (
                f"По запросу получено {n} строк. "
                "Краткое резюме модели пустое — смотрите таблицу результата ниже в чате."
            ),
            "report_ru": "",
        }
    if sql:
        return {
            "reply_ru": "Запрос выполнен; подходящих строк в выборке не найдено.",
            "report_ru": "",
        }
    return {
        "reply_ru": "Не удалось сформулировать ответ по данным (пустой результат модели).",
        "report_ru": "",
    }
