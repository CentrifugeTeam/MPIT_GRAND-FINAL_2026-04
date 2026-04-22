from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


class AnalyticsProxy:
    def __init__(self) -> None:
        self.base_url = settings.ANALYTICS_SERVICE_URL.rstrip("/")
        self.report_base_url = settings.REPORT_TASK_SERVICE_URL.rstrip("/")
        self.timeout = httpx.Timeout(180.0, connect=10.0)

    def _detail(self, response: httpx.Response) -> Any:
        try:
            body = response.json()
            if isinstance(body, dict) and "detail" in body:
                return body["detail"]
            return body
        except Exception:
            return response.text or response.reason_phrase

    async def interpret_question(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/interpret-question",
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

    async def create_nl_chat(self, user_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/chats",
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

    async def get_nl_chat_messages(
        self, user_id: str, conversation_id: str
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.base_url}/api/analytics/chats/{conversation_id}/messages",
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

    async def patch_nl_chat_title(
        self, user_id: str, conversation_id: str, title: str
    ) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.patch(
                    f"{self.base_url}/api/analytics/chats/{conversation_id}",
                    json={"title": title},
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

    async def delete_nl_chat(self, user_id: str, conversation_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.delete(
                    f"{self.base_url}/api/analytics/chats/{conversation_id}",
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

    def _sources_write_headers(self) -> dict[str, str]:
        t = (settings.ANALYTICS_SOURCES_WRITE_TOKEN or "").strip()
        if not t:
            return {}
        return {"X-Analytics-Sources-Write-Token": t}

    async def list_data_sources(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(f"{self.base_url}/api/analytics/data-sources")
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

    async def create_data_source(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/analytics/data-sources",
                    json=body,
                    headers=self._sources_write_headers(),
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

    async def patch_data_source(self, source_key: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.patch(
                    f"{self.base_url}/api/analytics/data-sources/{source_key}",
                    json=body,
                    headers=self._sources_write_headers(),
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

    async def delete_data_source(self, source_key: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.delete(
                    f"{self.base_url}/api/analytics/data-sources/{source_key}",
                    headers=self._sources_write_headers(),
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

    async def put_default_data_source(self, body: dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.put(
                    f"{self.base_url}/api/analytics/data-sources/default",
                    json=body,
                    headers=self._sources_write_headers(),
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

    async def create_report_task(self, user_id: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.report_base_url}/api/reports/tasks",
                    json=body,
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def list_report_tasks(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.report_base_url}/api/reports/tasks",
                    params={"limit": limit, "offset": offset},
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def get_report_task(self, user_id: str, task_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.report_base_url}/api/reports/tasks/{task_id}",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def patch_report_task(self, user_id: str, task_id: str, body: dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.patch(
                    f"{self.report_base_url}/api/reports/tasks/{task_id}",
                    json=body,
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))

    async def delete_report_task(self, user_id: str, task_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.delete(
                    f"{self.report_base_url}/api/reports/tasks/{task_id}",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))

    async def list_report_runs(
        self, user_id: str, task_id: str, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.report_base_url}/api/reports/tasks/{task_id}/reports",
                    params={"limit": limit, "offset": offset},
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def get_report_run(self, user_id: str, report_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.report_base_url}/api/reports/reports/{report_id}",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def list_report_runs_for_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(
                    f"{self.report_base_url}/api/reports/reports",
                    params={"limit": limit, "offset": offset},
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def create_report_run(self, user_id: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.report_base_url}/api/reports/reports",
                    json=body,
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
        return r.json()

    async def patch_report_run(self, user_id: str, report_id: str, body: dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.patch(
                    f"{self.report_base_url}/api/reports/reports/{report_id}",
                    json=body,
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))

    async def delete_report_run(self, user_id: str, report_id: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.delete(
                    f"{self.report_base_url}/api/reports/reports/{report_id}",
                    headers={"X-User-Id": user_id},
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Report task service unavailable: {e}",
            ) from e
        if r.is_error:
            raise HTTPException(status_code=r.status_code, detail=self._detail(r))
