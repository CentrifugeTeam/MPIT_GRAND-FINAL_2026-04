"""Redis-backed per-minute rate limit for /api/* (key: JWT uuid or client IP)."""

from __future__ import annotations

import logging
import time

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _bucket_key(request: Request) -> str:
    s = get_settings()
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            try:
                payload = jwt.decode(
                    token,
                    s.SECRET_KEY,
                    algorithms=[s.ALGORITHM],
                )
                uid = payload.get("uuid") or payload.get("sub")
                if uid:
                    return f"u:{uid}"
            except Exception:
                pass
    return f"ip:{_client_ip(request)}"


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        s = get_settings()
        redis_client = getattr(request.app.state, "redis_client", None)
        if not redis_client or not (s.REDIS_URL or "").strip():
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        limit = max(1, int(s.RATE_LIMIT_PER_MINUTE or 120))
        minute = int(time.time() // 60)
        rk = _bucket_key(request)
        redis_key = f"rl:bff:{rk}:{minute}"

        try:
            count = await redis_client.incr(redis_key)
            if count == 1:
                await redis_client.expire(redis_key, 90)
        except Exception as e:
            logger.warning("rate_limit redis error: %s", e)
            return await call_next(request)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests; try again in a minute."},
            )

        return await call_next(request)
