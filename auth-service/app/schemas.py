from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    role: str = Field(default="USER", max_length=64)


class UserCreate(UserBase):
    password: str
    confirm_password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(default=None, max_length=64)


class UserResponse(UserBase):
    uuid: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserResponse]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_uuid: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


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
