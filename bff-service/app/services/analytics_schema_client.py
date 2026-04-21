from typing import Any, Optional

import httpx

from app.core.config import get_settings


async def fetch_public_schema(source_key: Optional[str] = None) -> list[dict[str, Any]]:
    """Схема public из analytics-service (кэш на стороне analytics)."""
    s = get_settings()
    url = f"{s.ANALYTICS_SERVICE_URL.rstrip('/')}/api/analytics/schema"
    params: dict[str, str] = {"refresh": "false"}
    if source_key and str(source_key).strip():
        params["source_key"] = str(source_key).strip()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    tables = data.get("tables")
    if not isinstance(tables, list):
        return []
    return tables
