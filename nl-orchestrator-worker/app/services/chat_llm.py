from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import Settings, get_settings
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


def _merge_stream_segment(prev: str, segment: str) -> str:
    if not segment:
        return prev
    if not prev:
        return segment
    if len(segment) >= len(prev) and segment.startswith(prev):
        return segment
    if prev in segment and len(segment) > len(prev):
        return segment
    return prev + segment


def _stream_delta_parts(delta: dict[str, Any]) -> tuple[str, str]:
    """Фрагменты (reasoning_add, text_add) из choices[0].delta."""
    r_parts: list[str] = []
    t_parts: list[str] = []
    for key in ("reasoning", "reasoning_content", "thoughts"):
        v = delta.get(key)
        if isinstance(v, str) and v:
            r_parts.append(v)
    c = delta.get("content")
    if isinstance(c, str) and c:
        t_parts.append(c)
    elif isinstance(c, list):
        for p in c:
            if not isinstance(p, dict):
                continue
            t = str(p.get("type") or "").lower()
            if t in ("reasoning", "thinking", "thought"):
                b = p.get("text") or p.get("content")
                if b:
                    r_parts.append(str(b))
            else:
                tx = p.get("text") or p.get("content")
                if tx:
                    t_parts.append(str(tx))
    return ("".join(r_parts), "".join(t_parts))


def _extract_reasoning(data: dict[str, Any]) -> str:
    """Нативный reasoning/think из тела ответа провайдера (после include_reasoning / reasoning: enabled)."""
    try:
        choice = (data.get("choices") or [])[0] or {}
        message = choice.get("message") or {}
        candidates: list[Any] = [
            message.get("reasoning"),
            message.get("reasoning_content"),
            message.get("thoughts"),
            choice.get("reasoning"),
            data.get("reasoning"),
        ]
        details = data.get("reasoning_details")
        if isinstance(details, list):
            for item in details:
                if isinstance(item, dict):
                    candidates.append(item.get("text") or item.get("content") or item.get("reasoning"))
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    ptype = str(part.get("type") or "").lower()
                    if ptype in {"reasoning", "thinking", "thought"}:
                        candidates.append(part.get("text") or part.get("content"))
        texts = [str(x).strip() for x in candidates if isinstance(x, (str, int, float)) and str(x).strip()]
        if texts:
            joined = "\n\n".join(texts)
            return joined[:4000]
    except Exception:
        pass
    return ""


def _request_native_reasoning_payload(
    s: Settings, base_url_l: str, model_l: str
) -> dict[str, Any]:
    if not s.LLM_NATIVE_REASONING:
        return {}
    extra: dict[str, Any] = {}
    if "openrouter.ai" in base_url_l:
        extra["reasoning"] = {"enabled": True}
    if "openrouter.ai" in base_url_l and (
        "gemini" in model_l or "google/" in model_l or "gemma" in model_l
    ):
        extra["extra_body"] = {
            "google": {
                "thinking_config": {
                    "thinking_level": "low",
                    "include_thoughts": True,
                }
            }
        }
    return extra


async def _chat(messages: list[dict[str, str]], temperature: float = 0.2) -> tuple[str, str]:
    s = get_settings()
    if not s.LLM_API_KEY:
        raise ValueError("LLM_API_KEY не задан для nl-orchestrator-worker")
    url = s.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {s.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    base_url_l = s.LLM_BASE_URL.lower()
    model_l = s.LLM_MODEL.lower()
    payload: dict[str, Any] = {
        "model": s.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    payload.update(_request_native_reasoning_payload(s, base_url_l, model_l))
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    try:
        content = str(data["choices"][0]["message"]["content"])
        return content, _extract_reasoning(data)
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected LLM: {json.dumps(data)[:600]}") from e


async def _stream_chat(
    messages: list[dict[str, str]],
    temperature: float,
    on_reasoning: Callable[[str], Awaitable[None]],
    *,
    throttle_ms: float = 75.0,
    min_grow: int = 64,
) -> tuple[str, str]:
    """Стрим /chat/completions; по мере накопления вызывает on_reasoning(полный текст)."""
    s = get_settings()
    if not s.LLM_API_KEY:
        raise ValueError("LLM_API_KEY не задан для nl-orchestrator-worker")
    url = s.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {s.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    base_url_l = s.LLM_BASE_URL.lower()
    model_l = s.LLM_MODEL.lower()
    payload: dict[str, Any] = {
        "model": s.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    payload.update(_request_native_reasoning_payload(s, base_url_l, model_l))
    last_emit = 0.0
    last_len_emitted = 0
    reasoning_acc = ""
    text_acc = ""
    last_chunk: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data_s = line[6:].strip()
                    if data_s == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_s)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(chunk, dict):
                        continue
                    last_chunk = chunk
                    choices = chunk.get("choices") or []
                    if not choices or not isinstance(choices[0], dict):
                        continue
                    ch0 = choices[0]
                    fin = ch0.get("finish_reason")
                    delta = ch0.get("delta")
                    if not isinstance(delta, dict):
                        delta = {}
                    r_add, t_add = _stream_delta_parts(delta)
                    if r_add:
                        reasoning_acc = _merge_stream_segment(reasoning_acc, r_add)
                    if t_add:
                        text_acc += t_add
                    msg = ch0.get("message")
                    if isinstance(msg, dict):
                        mc = msg.get("content")
                        if isinstance(mc, str) and mc.strip() and not t_add:
                            text_acc = mc
                        r_msg = _extract_reasoning({"choices": [{"message": msg}]})
                        if r_msg and len(r_msg) > len(reasoning_acc):
                            reasoning_acc = r_msg
                    if reasoning_acc:
                        now = time.monotonic() * 1000.0
                        grow = len(reasoning_acc) - last_len_emitted
                        if now - last_emit >= throttle_ms or grow >= min_grow or fin is not None:
                            last_emit = now
                            last_len_emitted = len(reasoning_acc)
                            await on_reasoning(reasoning_acc[:4000])
    except (httpx.HTTPError, OSError) as e:
        logger.warning("LLM stream failed, one-shot: %s", e)
        raw, reas = await _chat(messages, temperature)
        if reas and on_reasoning:
            await on_reasoning(reas[:4000])
        return raw, reas
    if not text_acc.strip() and last_chunk:
        r2 = _extract_reasoning_from_stream_tail(last_chunk)
        if r2[0]:
            text_acc = r2[0]
        if r2[1] and len(r2[1]) > len(reasoning_acc):
            reasoning_acc = r2[1]
    if not text_acc.strip():
        raw, reas = await _chat(messages, temperature)
        if reas and on_reasoning and not reasoning_acc:
            await on_reasoning(reas[:4000])
        return raw, reas
    if not reasoning_acc.strip() and last_chunk:
        reasoning_acc = _extract_reasoning(last_chunk) or ""
    if on_reasoning and len(reasoning_acc) > last_len_emitted:
        await on_reasoning(reasoning_acc[:4000])
    return text_acc, (reasoning_acc or "")[:4000]


def _extract_reasoning_from_stream_tail(data: dict[str, Any]) -> tuple[str, str]:
    """Пытаемся достать content/reasoning из «хвостового» куска стрима."""
    try:
        ch = (data.get("choices") or [None])[0] or {}
        msg = ch.get("message")
        if isinstance(msg, dict):
            c = msg.get("content")
            t = str(c) if isinstance(c, str) else ""
            r = _extract_reasoning({"choices": [{"message": msg}]})
            return t, r
    except Exception:
        pass
    return "", ""


async def clarify_ambiguous_question(
    user_text: str,
    warnings: list[str],
    suggestions: list[str],
) -> str:
    """Короткий ответ-уточнение без SQL."""
    hints = "\n".join(f"- {w}" for w in (warnings or [])[:6])
    sug = "\n".join(f"- {s}" for s in (suggestions or [])[:6])
    sys = (
        "Пользователь задал короткий или неоднозначный аналитический вопрос по базе. "
        "Сформулируй ОДИН короткий уточняющий вопрос по-русски (1–2 предложения), без SQL и без данных."
    )
    user = f"Вопрос:\n{user_text}\n\nЗамечания:\n{hints or '(нет)'}\n\nПодсказки:\n{sug or '(нет)'}"
    raw, _ = await _chat(
        [{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.3,
    )
    return raw.strip()[:2000]


async def plan_turn(
    user_text: str,
    tables: list[TableSchema],
    history: list[dict[str, str]],
    *,
    active_source_label: Optional[str] = None,
    on_reasoning: Optional[Callable[[str], Awaitable[None]]] = None,
) -> dict[str, Any]:
    if _is_obviously_conversational(user_text):
        return {
            "reply_ru": _conversational_reply_ru(user_text),
            "sql_question": None,
            "sql_hints_ru": "",
            "reasoning": "",
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
    s = get_settings()
    if on_reasoning is not None and s.LLM_STREAM_REASONING:
        raw, reasoning = await _stream_chat(
            messages, 0.2, on_reasoning, throttle_ms=70.0, min_grow=48
        )
    else:
        raw, reasoning = await _chat(messages, temperature=0.2)
    try:
        out = _parse_json_obj(raw)
    except Exception as e:
        logger.warning("plan_turn JSON parse failed: %s", e)
        return {
            "reply_ru": raw[:2000],
            "sql_question": None,
            "sql_hints_ru": "",
            "reasoning": reasoning,
        }
    sq = out.get("sql_question")
    sql_q = None
    if isinstance(sq, str) and sq.strip():
        sql_q = sq.strip()
    return {
        "reply_ru": str(out.get("reply_ru") or "").strip(),
        "sql_question": sql_q,
        "sql_hints_ru": str(out.get("sql_hints_ru") or "").strip(),
        "reasoning": reasoning,
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
    *,
    on_reasoning: Optional[Callable[[str], Awaitable[None]]] = None,
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
    s = get_settings()
    if on_reasoning is not None and s.LLM_STREAM_REASONING:
        raw, reasoning = await _stream_chat(
            messages, 0.3, on_reasoning, throttle_ms=70.0, min_grow=48
        )
    else:
        raw, reasoning = await _chat(messages, temperature=0.3)
    try:
        out = _parse_json_obj(raw)
    except Exception as e:
        logger.warning("finalize JSON parse failed: %s", e)
        return {"reply_ru": raw[:4000], "report_ru": "", "reasoning": reasoning}
    reply = str(out.get("reply_ru") or "").strip()
    report = str(out.get("report_ru") or "").strip()
    if reply or report:
        return {"reply_ru": reply, "report_ru": report, "reasoning": reasoning}
    if error:
        return {
            "reply_ru": f"Ошибка выполнения SQL: {error}",
            "report_ru": "",
            "reasoning": reasoning,
        }
    if rows:
        n = len(rows)
        return {
            "reply_ru": (
                f"По запросу получено {n} строк. "
                "Краткое резюме модели пустое — смотрите таблицу результата ниже в чате."
            ),
            "report_ru": "",
            "reasoning": reasoning,
        }
    if sql:
        return {
            "reply_ru": "Запрос выполнен; подходящих строк в выборке не найдено.",
            "report_ru": "",
            "reasoning": reasoning,
        }
    return {
        "reply_ru": "Не удалось сформулировать ответ по данным (пустой результат модели).",
        "report_ru": "",
        "reasoning": reasoning,
    }
