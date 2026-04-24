import httpx
from typing import Dict, Any, List
from app.core.config import get_settings

settings = get_settings()

class NotificationService:
    def __init__(self):
        self.notification_service_url = settings.NOTIFICATION_SERVICE_URL

    async def create_notification(self, user_id: str, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать уведомление через notification-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.notification_service_url}/notifications/{user_id}",
                json=notification_data
            )
            response.raise_for_status()
            return response.json()

    async def delete_notification(self, user_id: str, notification_id: str) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.notification_service_url}/notifications/{user_id}/notification/{notification_id}"
            )
            response.raise_for_status()

    async def get_user_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Получить уведомления пользователя через notification-service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.notification_service_url}/notifications/{user_id}"
            )
            response.raise_for_status()
            return response.json()

    async def send_notification_to_queue(self, user_id: str, notification_data: Dict[str, Any]) -> str:
        """Отправить уведомление в очередь через notification-service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.notification_service_url}/notifications/{user_id}/notify",
                    json=notification_data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise e

    async def get_notification_settings(self, user_id: str) -> Dict[str, Any]:
        """Получить настройки уведомлений через notification-service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.notification_service_url}/notifications/{user_id}/settings"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise e

    async def update_notification_settings(self, user_id: str, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить настройки уведомлений через notification-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.notification_service_url}/notifications/{user_id}/settings",
                json=settings_data
            )
            response.raise_for_status()
            return response.json()
