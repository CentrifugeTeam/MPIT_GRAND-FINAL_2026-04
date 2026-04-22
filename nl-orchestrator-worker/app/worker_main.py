"""
NL Orchestrator: чат с пользователем (LLM) + постановка задач в nl_sql_generate_request
и приём ответов из nl_sql_generate_result_chat.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aio_pika
import httpx
from aio_pika import DeliveryMode, Message

from app.core.config import get_settings
from app.core.queues import (
    QUEUE_CHAT_INCOMING,
    QUEUE_CHAT_OUT,
    QUEUE_GENERATE_REQUEST,
    QUEUE_GENERATE_RESULT_CHAT,
    QUEUE_REPORT_TASK_INCOMING_V1,
)
from app.schemas.analytics import TableSchema
from app.services.chat_llm import clarify_ambiguous_question, finalize_after_sql, plan_turn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nl_orchestrator_worker")


@dataclass
class PendingCtx:
    conversation_id: str
    message_id_in: str
    user_text: str
    user_id: str
    scheduled_report: bool = False
    report_id: str | None = None
    task_id: str | None = None


pending: Dict[str, PendingCtx] = {}
_pending_lock = asyncio.Lock()

_WS_CHAT_TABLE_ROWS_CAP = 200


def _rows_as_dicts(columns: List[Any], rows: List[Any]) -> List[Dict[str, Any]]:
    """JSON из воркера обычно list[dict]; на всякий случай поддерживаем list[list] + columns."""
    col_names = [str(c) for c in columns] if isinstance(columns, list) else []
    out: List[Dict[str, Any]] = []
    for r in rows:
        if isinstance(r, dict):
            out.append(dict(r))
        elif isinstance(r, (list, tuple)) and col_names:
            out.append(
                {
                    col_names[i]: r[i]
                    for i in range(min(len(col_names), len(r)))
                }
            )
    return out


def _slim_chart_payload_for_ws(chart_payload: Any) -> dict[str, Any]:
    """Уменьшаем тело для WebSocket: для bar/line строки таблицы не нужны клиенту."""
    if not isinstance(chart_payload, dict):
        return {}
    cp: dict[str, Any] = dict(chart_payload)
    t = cp.get("type")
    if t in ("bar", "line"):
        cp.pop("rows", None)
    elif t == "table":
        rows = cp.get("rows")
        if isinstance(rows, list) and len(rows) > _WS_CHAT_TABLE_ROWS_CAP:
            cp["rows"] = rows[:_WS_CHAT_TABLE_ROWS_CAP]
    return cp


async def _publish_json(pub_channel: aio_pika.Channel, body: Dict[str, Any]) -> None:
    await pub_channel.default_exchange.publish(
        Message(
            body=json.dumps(body, default=str).encode("utf-8"),
            delivery_mode=DeliveryMode.PERSISTENT,
        ),
        routing_key=QUEUE_CHAT_OUT,
    )


async def _sync_chat_event(
    action: str,
    user_id: str,
    conversation_id: str,
    client_message_id: Optional[str],
    payload: Dict[str, Any],
) -> None:
    s = get_settings()
    base = (s.ANALYTICS_SERVICE_URL or "").strip().rstrip("/")
    if not base or not s.INTERNAL_NL_CHAT_SYNC_TOKEN:
        return
    url = f"{base}/api/analytics/internal/nl-chat-sync"
    body = {
        "action": action,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "client_message_id": client_message_id,
        "payload": payload,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                url,
                json=body,
                headers={"X-Chat-Sync-Token": s.INTERNAL_NL_CHAT_SYNC_TOKEN},
            )
            r.raise_for_status()
    except Exception as e:
        logger.warning("chat history sync failed: %s", e)


async def _send_report_notification(
    *,
    user_id: str,
    email: Optional[str],
    title: str,
    message: str,
) -> None:
    if not email:
        return
    s = get_settings()
    base = (s.NOTIFICATION_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return
    url = f"{base}/notifications/{user_id}/notify"
    body = {
        "type": "report",
        "title": title[:200] or "Плановый отчет",
        "message": message[:2000],
        "email": email,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
    except Exception as e:
        logger.warning("report notification failed: %s", e)


async def _resolve_user_email(user_id: str) -> Optional[str]:
    s = get_settings()
    base = (s.AUTH_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return None
    url = f"{base}/users/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("resolve user email failed for %s: %s", user_id, e)
        return None
    email = data.get("email") if isinstance(data, dict) else None
    if isinstance(email, str) and email.strip():
        return email.strip()
    return None


async def _fetch_schema_tables(
    source_key: str | None,
    *,
    user_id: str,
    user_role: str | None,
) -> list[dict[str, Any]]:
    s = get_settings()
    base = (s.ANALYTICS_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return []
    params: dict[str, Any] = {}
    if source_key:
        params["source_key"] = source_key
    headers = {
        "X-User-Id": str(user_id),
        "X-User-Role": (user_role or "USER").strip(),
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                f"{base}/api/analytics/schema",
                params=params,
                headers=headers,
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("schema fetch failed: %s", e)
        return []
    tables = data.get("tables") if isinstance(data, dict) else None
    return tables if isinstance(tables, list) else []


async def _fetch_interpretation(
    question: str,
    *,
    user_id: str,
    user_role: str | None,
    source_key: str | None,
) -> dict[str, Any] | None:
    s = get_settings()
    base = (s.ANALYTICS_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return None
    body: dict[str, Any] = {"question": question.strip()}
    if source_key:
        body["analytics_source_key"] = source_key
    headers = {
        "X-User-Id": str(user_id),
        "X-User-Role": (user_role or "USER").strip(),
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{base}/api/analytics/interpret-question",
                json=body,
                headers=headers,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning("interpret fetch failed: %s", e)
        return None


async def _report_run_done(
    report_id: str,
    result_summary: str,
    result_payload: dict[str, Any],
) -> None:
    s = get_settings()
    base = (s.REPORT_TASK_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return
    url = f"{base}/api/reports/internal/reports/{report_id}/result"
    body = {
        "status": "done",
        "result_summary": result_summary[:2000] if result_summary else None,
        "result_payload": result_payload,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                url,
                json=body,
                headers={"X-Report-Internal-Token": s.REPORT_TASK_INTERNAL_TOKEN},
            )
            r.raise_for_status()
    except Exception as e:
        logger.warning("report run done callback failed (%s): %s", report_id, e)


async def _report_run_failed(report_id: str, error: str) -> None:
    s = get_settings()
    base = (s.REPORT_TASK_SERVICE_URL or "").strip().rstrip("/")
    if not base:
        return
    url = f"{base}/api/reports/internal/reports/{report_id}/error"
    body = {"status": "failed", "error": error[:4000]}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                url,
                json=body,
                headers={"X-Report-Internal-Token": s.REPORT_TASK_INTERNAL_TOKEN},
            )
            r.raise_for_status()
    except Exception as e:
        logger.warning("report run failed callback failed (%s): %s", report_id, e)


async def _handle_chat_incoming(
    message: aio_pika.IncomingMessage,
    pub_channel: aio_pika.Channel,
) -> None:
    async with message.process():
        data = json.loads(message.body.decode("utf-8"))
        conv = str(data.get("conversation_id") or "").strip()
        uid = str(data.get("user_id") or "").strip()
        user_role = str(data.get("user_role") or "USER").strip()
        mid = str(data.get("message_id") or uuid.uuid4())
        content = str(data.get("content") or "").strip()
        scheduled_report = bool(data.get("scheduled_report"))
        if not conv or not content:
            return
        if conv != "__report_run__":
            await _sync_chat_event("user_message", uid, conv, mid, {"text": content})
        raw_source = data.get("analytics_source_key")
        sk_key = (
            str(raw_source).strip()
            if isinstance(raw_source, str) and str(raw_source).strip()
            else None
        )
        tables_raw = data.get("schema_tables") or []
        if not tables_raw:
            tables_raw = await _fetch_schema_tables(sk_key, user_id=uid, user_role=user_role)
        if not tables_raw:
            err_txt = "Нет схемы БД в запросе. Обновите страницу или откройте чат из раздела аналитики."
            if conv != "__report_run__":
                await _publish_json(
                    pub_channel,
                    {
                        "type": "chat_assistant",
                        "conversation_id": conv,
                        "message_id": mid,
                        "text": err_txt,
                        "sql": None,
                        "status": "error",
                    },
                )
                await _sync_chat_event(
                    "assistant_message",
                    uid,
                    conv,
                    mid,
                    {
                        "text": err_txt,
                        "report": "",
                        "sql": None,
                        "status": "error",
                        "error": err_txt,
                        "row_count": 0,
                        "chart": {"type": "table"},
                        "chart_payload": {},
                        "columns": [],
                        "rows": [],
                    },
                )
            report_id = str(data.get("report_id") or "").strip()
            if report_id:
                await _report_run_failed(report_id, err_txt)
            return
        tables = [TableSchema.model_validate(x) for x in tables_raw]
        s_cfg = get_settings()
        thr = float(getattr(s_cfg, "INTERPRET_CONFIDENCE_THRESHOLD", 0.45) or 0.45)
        interp_json = await _fetch_interpretation(
            content,
            user_id=uid,
            user_role=user_role,
            source_key=sk_key,
        )
        if (
            interp_json
            and conv != "__report_run__"
            and float(interp_json.get("interpretation_confidence") or 1.0) < thr
        ):
            warns = interp_json.get("interpretation_warnings") or []
            sugs = interp_json.get("interpretation_suggestions") or []
            if isinstance(warns, list) and warns:
                try:
                    clarify = await clarify_ambiguous_question(
                        content,
                        [str(x) for x in warns],
                        [str(x) for x in sugs if isinstance(sugs, list)],
                    )
                except Exception:
                    clarify = "Уточните, пожалуйста, метрику, период и разрез (группировку) для запроса к базе."
                if conv != "__report_run__":
                    await _publish_json(
                        pub_channel,
                        {
                            "type": "chat_assistant",
                            "conversation_id": conv,
                            "message_id": mid,
                            "text": clarify,
                            "sql": None,
                            "status": "done",
                        },
                    )
                    await _sync_chat_event(
                        "assistant_message",
                        uid,
                        conv,
                        mid,
                        {
                            "text": clarify,
                            "report": "",
                            "sql": None,
                            "status": "done",
                            "error": None,
                            "row_count": 0,
                            "chart": {"type": "table"},
                            "chart_payload": {},
                            "columns": [],
                            "rows": [],
                        },
                    )
                return

        hist_raw = data.get("history") or []
        history_norm: List[Dict[str, str]] = []
        for h in hist_raw:
            if isinstance(h, dict) and "role" in h and "content" in h:
                history_norm.append(
                    {"role": str(h["role"]), "content": str(h["content"])}
                )
        raw_lbl = data.get("analytics_source_label")
        active_lbl = (
            str(raw_lbl).strip()
            if isinstance(raw_lbl, str) and str(raw_lbl).strip()
            else None
        )
        plan = await plan_turn(
            content, tables, history_norm, active_source_label=active_lbl
        )
        sql_q = plan.get("sql_question")
        if sql_q:
            job_id = str(uuid.uuid4())
            turn_id = str(uuid.uuid4())
            async with _pending_lock:
                pending[job_id] = PendingCtx(
                    conversation_id=conv,
                    message_id_in=mid,
                    user_text=content,
                    user_id=uid,
                    scheduled_report=scheduled_report,
                    report_id=(str(data.get("report_id") or "").strip() or None),
                    task_id=(str(data.get("task_id") or "").strip() or None),
                )
            hints = (plan.get("sql_hints_ru") or "").strip() or None
            raw_max = data.get("max_rows")
            cap = int(getattr(get_settings(), "ORCH_GLOBAL_MAX_ROWS", 100_000) or 100_000)
            if isinstance(raw_max, int) and raw_max > 0:
                sql_max_rows = min(cap, raw_max)
            else:
                d = get_settings().CHAT_SQL_MAX_ROWS
                sql_max_rows = min(cap, d) if isinstance(d, int) and d > 0 else min(cap, 50_000)
            raw_src = data.get("analytics_source_key")
            analytics_source_key = (
                str(raw_src).strip() if isinstance(raw_src, str) and str(raw_src).strip() else None
            )
            allowed_names: list[str] = []
            for tr in tables_raw:
                if isinstance(tr, dict) and tr.get("name"):
                    allowed_names.append(str(tr["name"]).strip().lower())
            access_policy = {
                "allowed_tables": allowed_names or ["*"],
                "denied_columns": {},
            }
            sql_payload: Dict[str, Any] = {
                "job_id": job_id,
                "user_id": uid,
                "user_role": user_role,
                "question": sql_q,
                "schema_tables": tables_raw,
                "max_rows": sql_max_rows,
                "conversation_id": conv,
                "sql_turn_id": turn_id,
                "orchestrator_hints": hints,
                "glossary_context": data.get("glossary_context")
                if isinstance(data.get("glossary_context"), str)
                else None,
                "analytics_source_key": analytics_source_key,
                "access_policy": access_policy,
            }
            await pub_channel.default_exchange.publish(
                Message(
                    body=json.dumps(sql_payload, default=str).encode("utf-8"),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=QUEUE_GENERATE_REQUEST,
            )
            if conv != "__report_run__":
                await _publish_json(
                    pub_channel,
                    {
                        "type": "chat_sql_queued",
                        "conversation_id": conv,
                        "message_id": mid,
                        "job_id": job_id,
                        "sql_turn_id": turn_id,
                        "preface": plan.get("reply_ru") or "",
                    },
                )
                await _sync_chat_event(
                    "system_message",
                    uid,
                    conv,
                    f"sqlq-{turn_id}",
                    {
                        "text": plan.get("reply_ru") or "",
                        "variant": "sql_queued",
                    },
                )
        else:
            if conv != "__report_run__":
                await _publish_json(
                    pub_channel,
                    {
                        "type": "chat_assistant",
                        "conversation_id": conv,
                        "message_id": mid,
                        "text": plan.get("reply_ru") or "",
                        "sql": None,
                        "status": "done",
                    },
                )
                await _sync_chat_event(
                    "assistant_message",
                    uid,
                    conv,
                    mid,
                    {
                        "text": plan.get("reply_ru") or "",
                        "report": None,
                        "sql": None,
                        "status": "done",
                        "chart_payload": {},
                        "chart": {},
                        "columns": [],
                        "rows": [],
                        "row_count": None,
                        "error": None,
                    },
                )


async def _handle_sql_chat_result(
    message: aio_pika.IncomingMessage,
    pub_channel: aio_pika.Channel,
) -> None:
    async with message.process():
        data = json.loads(message.body.decode("utf-8"))
        jid = str(data.get("job_id") or "")
        if not jid:
            return
        async with _pending_lock:
            ctx = pending.pop(jid, None)
        if ctx is None:
            conv_orphan = str(data.get("conversation_id") or "").strip()
            uid_orphan = str(data.get("user_id") or "").strip()
            if conv_orphan:
                msg_id = f"orphan-{jid}"
                err_txt = (
                    "Результат SQL пришёл без контекста сессии (рестарт сервиса или рассинхрон). "
                    f"job_id={jid}. Отправьте вопрос ещё раз."
                )
                logger.warning(
                    "sql chat result: no pending ctx for job_id=%s conversation_id=%s",
                    jid,
                    conv_orphan,
                )
                sql_o = data.get("sql")
                sql_str = str(sql_o) if sql_o else None
                ws_orphan: Dict[str, Any] = {
                    "type": "chat_assistant",
                    "conversation_id": conv_orphan,
                    "message_id": msg_id,
                    "text": err_txt,
                    "report": "",
                    "sql": sql_str,
                    "status": "error",
                    "error": err_txt,
                    "row_count": data.get("row_count"),
                    "chart": {"type": "table"},
                    "chart_payload": {},
                    "columns": [],
                    "rows": [],
                }
                await _publish_json(pub_channel, ws_orphan)
                if uid_orphan:
                    await _sync_chat_event(
                        "assistant_message",
                        uid_orphan,
                        conv_orphan,
                        msg_id,
                        {
                            "text": err_txt,
                            "report": "",
                            "sql": sql_str,
                            "status": "error",
                            "error": err_txt,
                            "row_count": data.get("row_count"),
                            "chart": {"type": "table"},
                            "chart_payload": {},
                            "columns": [],
                            "rows": [],
                        },
                    )
            return
        status = str(data.get("status") or "")
        err: Optional[str] = data.get("error") if status == "error" else None
        if err is not None:
            err = str(err)
        sql = data.get("sql")
        sql_s = str(sql) if sql else None
        cols = data.get("columns") or []
        rows = data.get("rows") or []
        if not isinstance(cols, list):
            cols = []
        if not isinstance(rows, list):
            rows = []
        rows_dicts = _rows_as_dicts(cols, rows)
        try:
            final = await finalize_after_sql(
                ctx.user_text,
                sql_s,
                err,
                [str(c) for c in cols],
                rows_dicts,
            )
        except Exception as e:
            logger.exception("finalize_after_sql failed")
            final = {
                "reply_ru": f"Не удалось сформулировать ответ: {e}",
                "report_ru": "",
            }
        chart_raw = data.get("chart")
        chart_out: dict[str, Any] = (
            dict(chart_raw) if isinstance(chart_raw, dict) else {"type": "table"}
        )
        chart_payload_ws = _slim_chart_payload_for_ws(data.get("chart_payload"))
        rows_list = rows_dicts
        rows_ws = rows_list[:_WS_CHAT_TABLE_ROWS_CAP]

        ws_body: Dict[str, Any] = {
            "type": "chat_assistant",
            "conversation_id": ctx.conversation_id,
            "message_id": ctx.message_id_in,
            "text": final.get("reply_ru") or "",
            "report": final.get("report_ru") or "",
            "sql": sql_s,
            "status": status,
            "error": err,
            "row_count": data.get("row_count"),
            "chart": chart_out,
            "chart_payload": chart_payload_ws,
            "columns": [str(c) for c in cols],
            "rows": rows_ws,
        }
        if ctx.conversation_id != "__report_run__":
            await _publish_json(pub_channel, ws_body)
        sync_pl = {
            "text": final.get("reply_ru") or "",
            "report": final.get("report_ru") or "",
            "sql": sql_s,
            "status": status,
            "error": err,
            "row_count": data.get("row_count"),
            "chart": chart_out,
            "chart_payload": chart_payload_ws,
            "columns": [str(c) for c in cols],
            "rows": rows_ws,
        }
        if ctx.conversation_id != "__report_run__":
            await _sync_chat_event(
                "assistant_message",
                ctx.user_id,
                ctx.conversation_id,
                ctx.message_id_in,
                sync_pl,
            )
        elif ctx.report_id:
            if status == "done":
                await _report_run_done(
                    ctx.report_id,
                    (final.get("report_ru") or final.get("reply_ru") or "").strip(),
                    {
                        "sql": sql_s,
                        "row_count": data.get("row_count"),
                        "chart": chart_out,
                        "chart_payload": chart_payload_ws,
                        "columns": [str(c) for c in cols],
                        "rows": rows_ws,
                    },
                )
            else:
                await _report_run_failed(ctx.report_id, err or "Report execution failed")
        if status == "done" and ctx.scheduled_report:
            has_table = bool(rows_ws)
            has_chart = (
                (chart_out.get("type") in ("bar", "line"))
                or bool((chart_payload_ws or {}).get("series"))
                or bool((chart_payload_ws or {}).get("labels"))
            )
            summary = (final.get("report_ru") or final.get("reply_ru") or "Отчет готов.").strip()
            summary = summary[:900]
            if has_table or has_chart:
                summary = (
                    f"{summary}\n\n"
                    "Полный отчет с таблицами и визуализациями доступен в веб-интерфейсе. "
                    "Откройте раздел аналитики на сайте."
                )
            await _send_report_notification(
                user_id=ctx.user_id,
                email=await _resolve_user_email(ctx.user_id),
                title=ctx.user_text[:180] or "Плановый отчет",
                message=summary,
            )


async def _amain() -> None:
    s = get_settings()
    url = (
        f"amqp://{s.RABBITMQ_USER}:{s.RABBITMQ_PASSWORD}"
        f"@{s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}/"
    )
    delay = 1.0
    while True:
        try:
            connection = await aio_pika.connect_robust(url)
            break
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("RabbitMQ connect failed (%s). Retrying in %.1fs", e, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 15.0)

    async with connection:
        ch_cons = await connection.channel()
        ch_pub = await connection.channel()
        await ch_cons.set_qos(prefetch_count=2)
        await ch_pub.declare_queue(QUEUE_CHAT_OUT, durable=True)
        q_in = await ch_cons.declare_queue(QUEUE_CHAT_INCOMING, durable=True)
        q_report_v1 = await ch_cons.declare_queue(QUEUE_REPORT_TASK_INCOMING_V1, durable=True)
        q_sql = await ch_cons.declare_queue(QUEUE_GENERATE_RESULT_CHAT, durable=True)

        async def on_chat(msg: aio_pika.IncomingMessage) -> None:
            try:
                await _handle_chat_incoming(msg, ch_pub)
            except Exception:
                logger.exception("chat incoming handler failed")

        async def on_sql(msg: aio_pika.IncomingMessage) -> None:
            try:
                await _handle_sql_chat_result(msg, ch_pub)
            except Exception:
                logger.exception("sql chat result handler failed")

        await q_in.consume(on_chat)
        await q_report_v1.consume(on_chat)
        await q_sql.consume(on_sql)
        logger.info(
            "nl-orchestrator-worker ready (queues: %s, %s, %s → %s)",
            QUEUE_CHAT_INCOMING,
            QUEUE_REPORT_TASK_INCOMING_V1,
            QUEUE_GENERATE_RESULT_CHAT,
            QUEUE_GENERATE_REQUEST,
        )
        await asyncio.Future()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
