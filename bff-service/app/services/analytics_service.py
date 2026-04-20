from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


class AnalyticsProxy:
    def __init__(self) -> None:
        self.base_url = settings.ANALYTICS_SERVICE_URL.rstrip("/")
        self.timeout = httpx.Timeout(180.0, connect=10.0)

    def _detail(self, response: httpx.Response) -> Any:
        try:
            body = response.json()
            if isinstance(body, dict) and "detail" in body:
                return body["detail"]
            return body
        except Exception:
            return response.text or response.reason_phrase

    async def get_glossary(
        self,
        query: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params: dict[str, Any] = {"limit": limit}
                if query is not None and query != "":
                    params["q"] = query
                r = await client.get(
                    f"{self.base_url}/api/analytics/glossary",
                    params=params,
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def get_schema(self, refresh: bool) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.base_url}/api/analytics/schema",
                    params={"refresh": refresh},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def generate_sql(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/generate-sql",
                    json=payload,
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/execute",
                    json=payload,
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/ask",
                    json=payload,
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def ask_async(self, payload: dict[str, Any], user_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/ask-async",
                    json=payload,
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def get_job(self, job_id: str, user_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.base_url}/api/analytics/jobs/{job_id}",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def rerun_job(
        self,
        job_id: str,
        payload: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/jobs/{job_id}/rerun",
                    json=payload,
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()

    async def delete_job(self, job_id: str, user_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.delete(
                    f"{self.base_url}/api/analytics/jobs/{job_id}",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )

    async def delete_all_history(self, user_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.delete(
                    f"{self.base_url}/api/analytics/history",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )

    async def get_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.base_url}/api/analytics/history",
                    params={"limit": limit, "offset": offset},
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Analytics service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(
                status_code=r.status_code,
                detail=self._detail(r),
            )
        return r.json()
