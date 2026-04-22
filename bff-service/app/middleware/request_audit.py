"""Structured JSON lines to stdout for request auditing."""

from __future__ import annotations

import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("request_audit")


class RequestAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        request.state.request_id = rid
        t0 = time.perf_counter()
        response = None
        err_type: str | None = None
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            err_type = type(e).__name__
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            status = getattr(response, "status_code", 500) if response else 500
            if err_type:
                outcome = "exception"
            elif status >= 500:
                outcome = "server_error"
            elif status >= 400:
                outcome = "client_error"
            else:
                outcome = "ok"
            line = {
                "service": "bff-service",
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status_code": status,
                "duration_ms": elapsed_ms,
                "outcome": outcome,
                "error_type": err_type,
            }
            logger.info(json.dumps(line, ensure_ascii=False))
