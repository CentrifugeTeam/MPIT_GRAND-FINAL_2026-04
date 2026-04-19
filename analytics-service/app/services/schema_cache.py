import threading
import time
from typing import Any, Optional

_cache_lock = threading.Lock()
_payload: Optional[list[Any]] = None
_cached_at: float = 0.0


def get_cached(ttl_seconds: int) -> Optional[list[Any]]:
    global _payload, _cached_at
    with _cache_lock:
        if _payload is None:
            return None
        if time.monotonic() - _cached_at > ttl_seconds:
            _payload = None
            return None
        return _payload


def set_cached(items: list[Any]) -> None:
    global _payload, _cached_at
    with _cache_lock:
        _payload = items
        _cached_at = time.monotonic()


def invalidate() -> None:
    global _payload
    with _cache_lock:
        _payload = None
