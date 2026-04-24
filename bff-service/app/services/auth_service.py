import httpx
import jwt
from typing import Dict, Any
from urllib.parse import quote
from fastapi import HTTPException, status
from app.core.config import get_settings

settings = get_settings()


def _email_path(email: str) -> str:
    """Без кодирования `@` ломает path `/users/email/{email}` (остаётся только часть до @)."""
    return quote(email, safe="")


def _raise_auth_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    try:
        body = response.json()
        detail = body.get("detail", body)
    except Exception:
        detail = response.text or response.reason_phrase
    raise HTTPException(status_code=response.status_code, detail=detail)


class AuthService:
    def __init__(self):
        self.auth_service_url = settings.AUTH_SERVICE_URL
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать пользователя через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/users/",
                json=user_data,
            )
            _raise_auth_error(response)
            return response.json()

    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Аутентификация пользователя через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/auth/login",
                json={"email": email, "password": password},
            )
            _raise_auth_error(response)
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновить access токен через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            _raise_auth_error(response)
            return response.json()

    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Получить пользователя по email через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.auth_service_url}/users/email/{_email_path(email)}"
            )
            _raise_auth_error(response)
            return response.json()

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Получить пользователя по ID через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.auth_service_url}/users/{user_id}"
            )
            _raise_auth_error(response)
            return response.json()

    async def get_all_users(self) -> list[Dict[str, Any]]:
        """Получить всех пользователей через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.auth_service_url}/users/"
            )
            _raise_auth_error(response)
            return response.json()

    async def search_users_by_email(
        self,
        query: str,
        limit: int = 20,
        access_token: str | None = None,
    ) -> list[Dict[str, Any]]:
        """Поиск пользователей по части email через auth-service."""
        async with httpx.AsyncClient() as client:
            headers: Dict[str, str] = {}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            response = await client.get(
                f"{self.auth_service_url}/users/search",
                params={"query": query, "limit": limit},
                headers=headers,
            )
            _raise_auth_error(response)
            data = response.json()
            if isinstance(data, dict):
                users = data.get("users", [])
                return users if isinstance(users, list) else []
            return []

    async def update_user(self, email: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить пользователя через auth-service"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.auth_service_url}/users/email/{_email_path(email)}",
                json=user_data,
            )
            _raise_auth_error(response)
            return response.json()

    async def update_user_role(self, user_uuid: str, role) -> Dict[str, Any]:
        """Изменить роль пользователя через auth-service"""
        async with httpx.AsyncClient() as client:
            role_value = role.value if hasattr(role, 'value') else str(role)
            response = await client.put(
                f"{self.auth_service_url}/users/{user_uuid}/role",
                json={"role": role_value}
            )

            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            elif response.status_code == 400:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role"
                )

            _raise_auth_error(response)
            return response.json()

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Декодировать JWT токен"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTError:
            raise Exception("Invalid token")
