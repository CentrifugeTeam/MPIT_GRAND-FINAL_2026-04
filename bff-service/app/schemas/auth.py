from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": "USER",
            }
        }
    )
    email: EmailStr = Field(..., description="Почта нового пользователя")
    password: str = Field(..., min_length=1, description="Пароль")
    confirm_password: str = Field(..., min_length=1, description="Повтор пароля")
    role: str = Field(
        default="USER",
        max_length=64,
        description="Ключ роли из справочника (по умолчанию USER)",
    )

class UserLogin(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "user@example.com", "password": "StrongPass123!"}}
    )
    email: EmailStr = Field(..., description="Почта")
    password: str = Field(..., min_length=1, description="Пароль")


class UserUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "new.email@example.com", "role": "ANALYST"}},
    )
    email: Optional[EmailStr] = Field(default=None, description="Новая почта")
    role: Optional[str] = Field(default=None, max_length=64, description="Новая роль (если поддерживается)")

class UserResponse(BaseModel):
    uuid: str = Field(..., description="UUID пользователя")
    email: str = Field(..., description="Почта")
    role: str = Field(..., description="Ключ роли")

class UserListResponse(BaseModel):
    users: list[UserResponse]

class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str = Field(..., description="JWT access")
    refresh_token: str = Field(..., description="JWT refresh")
    token_type: str = Field(default="bearer", description="Тип токена (как в OAuth2)")
    expires_in: int = Field(..., description="TTL access в секундах")
    user_uuid: str = Field(..., description="UUID пользователя")

class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"refresh_token": "eyJhbGciOi..."}})
    refresh_token: str

class RoleUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"role": "ADMIN"}})
    role: str = Field(..., max_length=64, description="Новый ключ роли из справочника")


class UserCreatedResponse(BaseModel):
    """Ответ BFF после успешного создания пользователя через auth-service."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "User created successfully",
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
            },
        },
    )
    message: str = Field(..., description="Текст результата")
    uuid: str = Field(..., description="UUID созданного пользователя")


class LogoutResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"message": "Successfully logged out"}},
    )
    message: str = Field(..., description="Результат выхода")
