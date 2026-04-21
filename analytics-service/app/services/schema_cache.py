import threading
import time
from typing import Any, Optional

_cache_lock = threading.Lock()
_payloads: dict[str, list[Any]] = {}
_cached_at: dict[str, float] = {}


def _norm_key(source_key: Optional[str]) -> str:
    s = (source_key or "").strip()
    return s if s else "__default__"


def get_cached(ttl_seconds: int, source_key: Optional[str] = None) -> Optional[list[Any]]:
    k = _norm_key(source_key)
    with _cache_lock:
        payload = _payloads.get(k)
        ts = _cached_at.get(k, 0.0)
        if payload is None:
            return None
        if time.monotonic() - ts > ttl_seconds:
            _payloads.pop(k, None)
            _cached_at.pop(k, None)
            return None
        return payload


def set_cached(items: list[Any], source_key: Optional[str] = None) -> None:
    k = _norm_key(source_key)
    with _cache_lock:
        _payloads[k] = items
        _cached_at[k] = time.monotonic()


def invalidate() -> None:
    with _cache_lock:
        _payloads.clear()
        _cached_at.clear()


def invalidate_key(source_key: Optional[str] = None) -> None:
    k = _norm_key(source_key)
    with _cache_lock:
        _payloads.pop(k, None)
        _cached_at.pop(k, None)
