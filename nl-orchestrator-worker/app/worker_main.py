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
)
from app.schemas.analytics import TableSchema
from app.services.chat_llm import finalize_after_sql, plan_turn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nl_orchestrator_worker")


@dataclass
class PendingCtx:
    conversation_id: str
    message_id_in: str
    user_text: str
    user_id: str


pending: Dict[str, PendingCtx] = {}
_pending_lock = asyncio.Lock()

_WS_CHAT_TABLE_ROWS_CAP = 200


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


async def _handle_chat_incoming(
    message: aio_pika.IncomingMessage,
    pub_channel: aio_pika.Channel,
) -> None:
    async with message.process():
        data = json.loads(message.body.decode("utf-8"))
        conv = str(data.get("conversation_id") or "").strip()
        uid = str(data.get("user_id") or "").strip()
        mid = str(data.get("message_id") or uuid.uuid4())
        content = str(data.get("content") or "").strip()
        if not conv or not content:
            return
        await _sync_chat_event("user_message", uid, conv, mid, {"text": content})
        tables_raw = data.get("schema_tables") or []
        if not tables_raw:
            await _publish_json(
                pub_channel,
                {
                    "type": "chat_assistant",
                    "conversation_id": conv,
                    "message_id": mid,
                    "text": "Нет схемы БД в запросе. Обновите страницу или откройте чат из раздела аналитики.",
                    "sql": None,
                    "status": "error",
                },
            )
            return
        tables = [TableSchema.model_validate(x) for x in tables_raw]
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
                )
            hints = (plan.get("sql_hints_ru") or "").strip() or None
            raw_max = data.get("max_rows")
            if isinstance(raw_max, int) and raw_max > 0:
                sql_max_rows = min(50_000_000, raw_max)
            else:
                d = get_settings().CHAT_SQL_MAX_ROWS
                sql_max_rows = min(50_000_000, d) if isinstance(d, int) and d > 0 else 50_000
            raw_src = data.get("analytics_source_key")
            analytics_source_key = (
                str(raw_src).strip() if isinstance(raw_src, str) and str(raw_src).strip() else None
            )
            sql_payload: Dict[str, Any] = {
                "job_id": job_id,
                "user_id": uid,
                "question": sql_q,
                "template_key": None,
                "schema_tables": tables_raw,
                "max_rows": sql_max_rows,
                "conversation_id": conv,
                "sql_turn_id": turn_id,
                "orchestrator_hints": hints,
                "glossary_context": data.get("glossary_context")
                if isinstance(data.get("glossary_context"), str)
                else None,
                "interpretation": None,
                "analytics_source_key": analytics_source_key,
            }
            await pub_channel.default_exchange.publish(
                Message(
                    body=json.dumps(sql_payload, default=str).encode("utf-8"),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=QUEUE_GENERATE_REQUEST,
            )
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
        try:
            final = await finalize_after_sql(
                ctx.user_text,
                sql_s,
                err,
                [str(c) for c in cols],
                [dict(r) for r in rows if isinstance(r, dict)],
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
        rows_list = [dict(r) for r in rows if isinstance(r, dict)]
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
        await _sync_chat_event(
            "assistant_message",
            ctx.user_id,
            ctx.conversation_id,
            ctx.message_id_in,
            sync_pl,
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
        await q_sql.consume(on_sql)
        logger.info(
            "nl-orchestrator-worker ready (queues: %s, %s → %s)",
            QUEUE_CHAT_INCOMING,
            QUEUE_GENERATE_RESULT_CHAT,
            QUEUE_GENERATE_REQUEST,
        )
        await asyncio.Future()


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
