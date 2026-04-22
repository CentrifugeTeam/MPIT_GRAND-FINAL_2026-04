"""Redact secrets from free text before LLM / logs."""

from __future__ import annotations

import re

_URI_CREDS = re.compile(
    r"\b(?:postgresql|postgres|mysql|mongodb|redis)://[^\s'\"]+@[^\s'\"]+",
    re.IGNORECASE,
)
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\b")
_API_KEY_KV = re.compile(
    r"\b(api[_-]?key|password|secret|token)\s*[:=]\s*[^\s&]+",
    re.IGNORECASE,
)


def redact_sensitive_text(text: str, *, placeholder: str = "[REDACTED]") -> str:
    if not text or not isinstance(text, str):
        return text
    out = _URI_CREDS.sub(placeholder, text)
    out = _BEARER.sub(f"Bearer {placeholder}", out)
    out = _API_KEY_KV.sub(lambda m: f"{m.group(1)}={placeholder}", out)
    return out
