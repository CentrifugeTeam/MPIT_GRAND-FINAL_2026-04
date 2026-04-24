from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import and_

from app.db.platform_models import AnalyticsChatSuggestion
from app.db.platform_session import PlatformSessionLocal
from app.services.data_sources_store import get_default_source_key

MAX_TOPICS = 5
QUESTIONS_PER_TOPIC = 4
MAX_QUESTIONS_TOTAL = MAX_TOPICS * QUESTIONS_PER_TOPIC
_TOPIC_KEY_RE = re.compile(r"[^a-z0-9-]+")


def _normalize_locale(locale: str | None) -> str:
    v = (locale or "ru").strip().lower()
    return v or "ru"


def _normalize_topic_key(raw: str, fallback_idx: int) -> str:
    k = _TOPIC_KEY_RE.sub("-", raw.strip().lower()).strip("-")
    if not k:
        return f"topic-{fallback_idx + 1}"
    return k[:64]


def _grouped_rows(rows: list[AnalyticsChatSuggestion]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for r in rows:
        tkey = (r.topic_key or "").strip()
        if not tkey:
            continue
        node = buckets.get(tkey)
        if node is None:
            node = {
                "topic_key": tkey,
                "topic_label": (r.topic_label or "").strip() or tkey,
                "topic_sort": int(r.topic_sort or 0),
                "questions": [],
            }
            buckets[tkey] = node
        node["questions"].append(
            {
                "text": (r.question_text or "").strip(),
                "question_sort": int(r.question_sort or 0),
            }
        )
    out: list[dict[str, Any]] = []
    topics = sorted(
        buckets.values(),
        key=lambda x: (int(x["topic_sort"]), str(x["topic_label"]).lower()),
    )[:MAX_TOPICS]
    for t in topics:
        questions = [
            q["text"]
            for q in sorted(t["questions"], key=lambda x: int(x["question_sort"]))
            if isinstance(q["text"], str) and q["text"].strip()
        ][:QUESTIONS_PER_TOPIC]
        if len(questions) < QUESTIONS_PER_TOPIC:
            continue
        out.append(
            {
                "topic_key": t["topic_key"],
                "topic_label": t["topic_label"],
                "questions": questions,
            }
        )
    return out


def list_chat_suggestions(
    source_key: str | None,
    locale: str | None = "ru",
) -> list[dict[str, Any]]:
    locale_norm = _normalize_locale(locale)
    sk = (source_key or "").strip().lower() or None
    with PlatformSessionLocal() as db:
        if sk:
            rows = (
                db.query(AnalyticsChatSuggestion)
                .filter(
                    and_(
                        AnalyticsChatSuggestion.is_active.is_(True),
                        AnalyticsChatSuggestion.locale == locale_norm,
                        AnalyticsChatSuggestion.source_key == sk,
                    )
                )
                .order_by(
                    AnalyticsChatSuggestion.topic_sort.asc(),
                    AnalyticsChatSuggestion.question_sort.asc(),
                    AnalyticsChatSuggestion.created_at.asc(),
                )
                .all()
            )
            grouped = _grouped_rows(rows)
            if grouped:
                return grouped
        dsk = get_default_source_key()
        if dsk and dsk != sk:
            rows_default = (
                db.query(AnalyticsChatSuggestion)
                .filter(
                    and_(
                        AnalyticsChatSuggestion.is_active.is_(True),
                        AnalyticsChatSuggestion.locale == locale_norm,
                        AnalyticsChatSuggestion.source_key == dsk,
                    )
                )
                .order_by(
                    AnalyticsChatSuggestion.topic_sort.asc(),
                    AnalyticsChatSuggestion.question_sort.asc(),
                    AnalyticsChatSuggestion.created_at.asc(),
                )
                .all()
            )
            grouped_default = _grouped_rows(rows_default)
            if grouped_default:
                return grouped_default
        rows_global = (
            db.query(AnalyticsChatSuggestion)
            .filter(
                and_(
                    AnalyticsChatSuggestion.is_active.is_(True),
                    AnalyticsChatSuggestion.locale == locale_norm,
                    AnalyticsChatSuggestion.source_key.is_(None),
                )
            )
            .order_by(
                AnalyticsChatSuggestion.topic_sort.asc(),
                AnalyticsChatSuggestion.question_sort.asc(),
                AnalyticsChatSuggestion.created_at.asc(),
            )
            .all()
        )
        return _grouped_rows(rows_global)


def get_system_suggestions_stats(source_key: str, locale: str | None = "ru") -> dict[str, int]:
    sk = (source_key or "").strip().lower()
    if not sk:
        return {"topics": 0, "questions": 0}
    locale_norm = _normalize_locale(locale)
    with PlatformSessionLocal() as db:
        rows = (
            db.query(AnalyticsChatSuggestion.topic_key, AnalyticsChatSuggestion.question_text)
            .filter(
                and_(
                    AnalyticsChatSuggestion.source_key == sk,
                    AnalyticsChatSuggestion.locale == locale_norm,
                    AnalyticsChatSuggestion.is_system.is_(True),
                    AnalyticsChatSuggestion.is_active.is_(True),
                )
            )
            .all()
        )
    topics = set()
    questions = 0
    for topic_key, question_text in rows:
        tk = str(topic_key or "").strip()
        qt = str(question_text or "").strip()
        if not tk or not qt:
            continue
        topics.add(tk)
        questions += 1
    return {"topics": min(len(topics), MAX_TOPICS), "questions": min(questions, MAX_QUESTIONS_TOTAL)}


def upsert_system_chat_suggestions(
    source_key: str,
    topics: list[dict[str, Any]],
    locale: str | None = "ru",
) -> int:
    sk = (source_key or "").strip().lower()
    if not sk:
        return 0
    locale_norm = _normalize_locale(locale)
    prepared: list[AnalyticsChatSuggestion] = []
    for ti, topic in enumerate(topics[:MAX_TOPICS]):
        label = str(topic.get("topic_label") or "").strip()
        if not label:
            continue
        topic_key = _normalize_topic_key(str(topic.get("topic_key") or label), ti)
        raw_questions = topic.get("questions")
        if not isinstance(raw_questions, list):
            continue
        uniq: list[str] = []
        seen: set[str] = set()
        for q in raw_questions:
            v = str(q or "").strip()
            if not v:
                continue
            key = v.lower()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(v)
            if len(uniq) >= QUESTIONS_PER_TOPIC:
                break
        if len(uniq) < QUESTIONS_PER_TOPIC:
            continue
        for qi, text in enumerate(uniq):
            prepared.append(
                AnalyticsChatSuggestion(
                    source_key=sk,
                    locale=locale_norm,
                    topic_key=topic_key,
                    topic_label=label[:255],
                    question_text=text[:4000],
                    topic_sort=ti,
                    question_sort=qi,
                    is_system=True,
                    is_active=True,
                )
            )
    if not prepared:
        return 0
    with PlatformSessionLocal.begin() as db:
        db.query(AnalyticsChatSuggestion).filter(
            and_(
                AnalyticsChatSuggestion.source_key == sk,
                AnalyticsChatSuggestion.locale == locale_norm,
                AnalyticsChatSuggestion.is_system.is_(True),
            )
        ).delete(synchronize_session=False)
        for row in prepared:
            db.add(row)
    return len(prepared)


def list_source_keys_without_system_chat_suggestions(locale: str | None = "ru") -> list[str]:
    from app.services.data_sources_store import list_active_source_keys

    locale_norm = _normalize_locale(locale)
    out: list[str] = []
    for sk in list_active_source_keys():
        stat = get_system_suggestions_stats(sk, locale=locale_norm)
        if stat["questions"] < QUESTIONS_PER_TOPIC:
            out.append(sk)
    return out


def mark_source_system_chat_suggestions_stale(source_key: str, locale: str | None = "ru") -> int:
    sk = (source_key or "").strip().lower()
    if not sk:
        return 0
    locale_norm = _normalize_locale(locale)
    now = datetime.utcnow()
    with PlatformSessionLocal.begin() as db:
        rows = (
            db.query(AnalyticsChatSuggestion)
            .filter(
                and_(
                    AnalyticsChatSuggestion.source_key == sk,
                    AnalyticsChatSuggestion.locale == locale_norm,
                    AnalyticsChatSuggestion.is_system.is_(True),
                    AnalyticsChatSuggestion.is_active.is_(True),
                )
            )
            .all()
        )
        for row in rows:
            row.is_active = False
            row.updated_at = now
        return len(rows)
