from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import func

from app.core.config import get_settings
from app.db.platform_models import AnalyticsDataSource
from app.db.platform_session import PlatformSessionLocal


_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


def normalize_source_key(key: str) -> str:
    k = key.strip().lower()
    if not _KEY_RE.match(k):
        raise ValueError(
            "source_key: только a-z, 0-9, дефис, 1–63 символа, с буквы или цифры",
        )
    return k


def _parse_sources_json(raw: str) -> list[tuple[str, str, str]]:
    """Возвращает (source_key, database_url, display_name)."""
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("ANALYTICS_SOURCES_JSON: ожидается JSON-массив")
    out: list[tuple[str, str, str]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"ANALYTICS_SOURCES_JSON: элемент {i} не объект")
        sk = normalize_source_key(str(item.get("key") or item.get("source_key") or ""))
        url = str(item.get("database_url") or item.get("url") or "").strip()
        if not url:
            raise ValueError(f"ANALYTICS_SOURCES_JSON: у «{sk}» нет database_url")
        dn = str(item.get("display_name") or item.get("name") or sk).strip() or sk
        out.append((sk, url, dn))
    return out


def _parse_sources_inline(raw: str) -> list[tuple[str, str, str]]:
    """
    Формат: key|url||key2|url2 (двойной || между источниками).
    Опционально третий сегмент: key|url|отображаемое имя (URL не должен содержать символ |).
    """
    chunks = [c.strip() for c in raw.split("||") if c.strip()]
    out: list[tuple[str, str, str]] = []
    for c in chunks:
        parts = [p.strip() for p in c.split("|")]
        if len(parts) < 2:
            raise ValueError(
                "ANALYTICS_SOURCES_INLINE: каждый блок key|url или key|url|display_name, разделитель источников — ||",
            )
        sk = normalize_source_key(parts[0])
        url = parts[1].strip()
        if not url:
            raise ValueError(f"ANALYTICS_SOURCES_INLINE: пустой URL для «{sk}»")
        dn = parts[2].strip() if len(parts) > 2 and parts[2].strip() else sk
        out.append((sk, url, dn))
    return out


def seed_data_sources_if_empty() -> None:
    """Первый запуск: из env или одна запись из ANALYTICS_DATABASE_URL."""
    settings = get_settings()
    db = PlatformSessionLocal()
    try:
        n = db.query(func.count(AnalyticsDataSource.id)).scalar() or 0
        if int(n) > 0:
            return
        rows: list[tuple[str, str, str]] = []
        js = (settings.ANALYTICS_SOURCES_JSON or "").strip()
        inline = (settings.ANALYTICS_SOURCES_INLINE or "").strip()
        if js:
            rows = _parse_sources_json(js)
        elif inline:
            rows = _parse_sources_inline(inline)
        else:
            dk = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "default").strip().lower()
            if not _KEY_RE.match(dk):
                dk = "default"
            rows = [(dk, settings.ANALYTICS_DATABASE_URL, dk)]
        default_key = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip().lower()
        if not default_key or not any(r[0] == default_key for r in rows):
            default_key = rows[0][0]
        for sk, url, dn in rows:
            db.add(
                AnalyticsDataSource(
                    source_key=sk,
                    display_name=dn,
                    database_url=url,
                    is_default=(sk == default_key),
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def sync_analytics_sources_from_env() -> None:
    """
    Если заданы ANALYTICS_SOURCES_JSON / INLINE — обновить или добавить строки в БД
    (чтобы после смены compose/.env список источников подтягивался без ручной очистки таблицы).
    """
    settings = get_settings()
    js = (settings.ANALYTICS_SOURCES_JSON or "").strip()
    inline = (settings.ANALYTICS_SOURCES_INLINE or "").strip()
    if not js and not inline:
        return
    try:
        if js:
            rows = _parse_sources_json(js)
        else:
            rows = _parse_sources_inline(inline)
    except Exception:
        return
    default_key = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip().lower()
    if not default_key or not any(r[0] == default_key for r in rows):
        default_key = rows[0][0]
    db = PlatformSessionLocal()
    try:
        for sk, url, dn in rows:
            row = (
                db.query(AnalyticsDataSource)
                .filter(AnalyticsDataSource.source_key == sk)
                .one_or_none()
            )
            if row:
                row.database_url = url.strip()
                row.display_name = dn.strip() or sk
                row.updated_at = datetime.utcnow()
            else:
                db.add(
                    AnalyticsDataSource(
                        source_key=sk,
                        display_name=dn.strip() or sk,
                        database_url=url.strip(),
                        is_default=False,
                    )
                )
        db.query(AnalyticsDataSource).update(
            {AnalyticsDataSource.is_default: False},
            synchronize_session=False,
        )
        n_def = (
            db.query(AnalyticsDataSource)
            .filter(AnalyticsDataSource.source_key == default_key)
            .update(
                {AnalyticsDataSource.is_default: True},
                synchronize_session=False,
            )
        )
        if int(n_def or 0) == 0:
            db.query(AnalyticsDataSource).filter(
                AnalyticsDataSource.source_key == rows[0][0]
            ).update(
                {AnalyticsDataSource.is_default: True},
                synchronize_session=False,
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    from app.services import schema_cache
    from app.services.analytics_db import dispose_analytics_engine_cache

    dispose_analytics_engine_cache()
    schema_cache.invalidate()


def list_sources_public() -> list[dict[str, Any]]:
    db = PlatformSessionLocal()
    try:
        rows = (
            db.query(AnalyticsDataSource)
            .order_by(AnalyticsDataSource.is_default.desc(), AnalyticsDataSource.source_key)
            .all()
        )
        return [
            {
                "key": r.source_key,
                "display_name": r.display_name,
                "is_default": bool(r.is_default),
            }
            for r in rows
        ]
    finally:
        db.close()


def get_default_source_key() -> Optional[str]:
    """Сначала ключ из DEFAULT_ANALYTICS_SOURCE_KEY (если строка есть в БД), иначе флаг is_default в БД."""
    settings = get_settings()
    env_pref = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip().lower()
    db = PlatformSessionLocal()
    try:
        if env_pref:
            row_env = (
                db.query(AnalyticsDataSource)
                .filter(AnalyticsDataSource.source_key == env_pref)
                .one_or_none()
            )
            if row_env:
                return row_env.source_key
        row = (
            db.query(AnalyticsDataSource)
            .filter(AnalyticsDataSource.is_default.is_(True))
            .one_or_none()
        )
        if row:
            return row.source_key
        row2 = db.query(AnalyticsDataSource).order_by(AnalyticsDataSource.source_key).first()
        return row2.source_key if row2 else None
    finally:
        db.close()


def list_active_source_keys() -> list[str]:
    db = PlatformSessionLocal()
    try:
        keys = [r[0] for r in db.query(AnalyticsDataSource.source_key).all()]
        return sorted(keys)
    finally:
        db.close()


def resolve_database_url(source_key: Optional[str]) -> str:
    """URL для подключения к данным; source_key None — сначала DEFAULT_ANALYTICS_SOURCE_KEY, затем is_default в БД."""
    settings = get_settings()
    sk = (source_key or "").strip().lower() or None
    env_pref = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip().lower()
    db = PlatformSessionLocal()
    try:
        if sk:
            row = (
                db.query(AnalyticsDataSource)
                .filter(AnalyticsDataSource.source_key == sk)
                .one_or_none()
            )
            if row:
                return row.database_url.strip()
        if env_pref:
            row_env = (
                db.query(AnalyticsDataSource)
                .filter(AnalyticsDataSource.source_key == env_pref)
                .one_or_none()
            )
            if row_env:
                return row_env.database_url.strip()
        row_d = (
            db.query(AnalyticsDataSource)
            .filter(AnalyticsDataSource.is_default.is_(True))
            .one_or_none()
        )
        if row_d:
            return row_d.database_url.strip()
        row_any = db.query(AnalyticsDataSource).order_by(AnalyticsDataSource.source_key).first()
        if row_any:
            return row_any.database_url.strip()
    finally:
        db.close()
    return settings.ANALYTICS_DATABASE_URL.strip()


def create_source(key: str, display_name: str, database_url: str, set_as_default: bool) -> dict:
    sk = normalize_source_key(key)
    db = PlatformSessionLocal()
    try:
        exists = (
            db.query(AnalyticsDataSource).filter(AnalyticsDataSource.source_key == sk).first()
        )
        if exists:
            raise ValueError("источник с таким key уже есть")
        cnt = int(db.query(func.count(AnalyticsDataSource.id)).scalar() or 0)
        is_def = bool(set_as_default or cnt == 0)
        if is_def:
            db.query(AnalyticsDataSource).update({AnalyticsDataSource.is_default: False})
        row = AnalyticsDataSource(
            source_key=sk,
            display_name=display_name.strip() or sk,
            database_url=database_url.strip(),
            is_default=is_def,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "key": row.source_key,
            "display_name": row.display_name,
            "is_default": bool(row.is_default),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_source(
    key: str,
    *,
    display_name: Optional[str] = None,
    database_url: Optional[str] = None,
    is_default: Optional[bool] = None,
) -> Optional[dict]:
    sk = normalize_source_key(key)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(AnalyticsDataSource)
            .filter(AnalyticsDataSource.source_key == sk)
            .one_or_none()
        )
        if not row:
            return None
        if display_name is None and database_url is None and is_default is None:
            return {
                "key": row.source_key,
                "display_name": row.display_name,
                "is_default": bool(row.is_default),
            }
        if display_name is not None:
            row.display_name = display_name.strip() or sk
        if database_url is not None:
            row.database_url = database_url.strip()
        if is_default is True:
            db.query(AnalyticsDataSource).update({AnalyticsDataSource.is_default: False})
            row.is_default = True
        elif is_default is False and row.is_default:
            other = (
                db.query(AnalyticsDataSource)
                .filter(AnalyticsDataSource.source_key != sk)
                .first()
            )
            if not other:
                raise ValueError("нельзя снять default — это единственный источник")
            row.is_default = False
            other.is_default = True
        row.updated_at = datetime.utcnow()
        db.commit()
        return {
            "key": row.source_key,
            "display_name": row.display_name,
            "is_default": bool(row.is_default),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def set_default_source(key: str) -> bool:
    sk = normalize_source_key(key)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(AnalyticsDataSource)
            .filter(AnalyticsDataSource.source_key == sk)
            .one_or_none()
        )
        if not row:
            return False
        db.query(AnalyticsDataSource).update({AnalyticsDataSource.is_default: False})
        row.is_default = True
        row.updated_at = datetime.utcnow()
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_source(key: str) -> bool:
    sk = normalize_source_key(key)
    db = PlatformSessionLocal()
    try:
        row = (
            db.query(AnalyticsDataSource)
            .filter(AnalyticsDataSource.source_key == sk)
            .one_or_none()
        )
        if not row:
            return False
        was_default = row.is_default
        db.delete(row)
        db.commit()
        if was_default:
            nxt = db.query(AnalyticsDataSource).order_by(AnalyticsDataSource.source_key).first()
            if nxt:
                nxt.is_default = True
                db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
