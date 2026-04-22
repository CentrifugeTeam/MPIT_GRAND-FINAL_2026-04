from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Почта пользователя")
    role: str = Field(
        default="USER",
        max_length=64,
        description="Ключ роли из role_definitions",
    )


class UserCreate(UserBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "role": "USER",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            }
        }
    }
    password: str = Field(..., min_length=1, description="Пароль")
    confirm_password: str = Field(..., min_length=1, description="Подтверждение пароля")


class UserLogin(BaseModel):
    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "secret"}}}
    email: EmailStr = Field(..., description="Почта")
    password: str = Field(..., min_length=1, description="Пароль")


class UserUpdate(BaseModel):
    model_config = {"json_schema_extra": {"example": {"email": "new@example.com", "role": "ANALYST"}}}
    email: Optional[EmailStr] = Field(default=None, description="Новая почта")
    role: Optional[str] = Field(default=None, max_length=64, description="Новая роль из справочника")


class UserResponse(UserBase):
    uuid: UUID = Field(..., description="UUID пользователя")
    is_active: bool = Field(..., description="Активен ли аккаунт")
    is_verified: bool = Field(..., description="Подтверждён ли email")
    created_at: datetime = Field(..., description="Создан")
    updated_at: Optional[datetime] = Field(default=None, description="Последнее обновление")

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserResponse]


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access")
    refresh_token: str = Field(..., description="JWT refresh")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(..., description="TTL access в секундах")
    user_uuid: str = Field(..., description="UUID пользователя")


class RefreshTokenRequest(BaseModel):
    model_config = {"json_schema_extra": {"example": {"refresh_token": "eyJ..."}}}
    refresh_token: str = Field(..., description="Refresh-токен из ответа login")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Текст результата операции")


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str


class RoleUpdate(BaseModel):
    role: str = Field(..., max_length=64)

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        return v.strip().upper().replace(" ", "_")


class RoleDefinitionBase(BaseModel):
    key: str = Field(..., max_length=64, description="UPPER_SNAKE_CASE key")
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class RoleDefinitionCreate(RoleDefinitionBase):
    @field_validator("key")
    @classmethod
    def normalize_key(cls, v: str) -> str:
        k = v.strip().upper().replace(" ", "_")
        if not k.replace("_", "").isalnum():
            raise ValueError("Invalid role key")
        return k


class RoleDefinitionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None


class RoleDefinitionResponse(BaseModel):
    key: str
    title: str
    description: Optional[str] = None
    is_system: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleDefinitionListResponse(BaseModel):
    roles: list[RoleDefinitionResponse]
