from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            }
        }
    )
    email: EmailStr
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "user@example.com", "password": "StrongPass123!"}}
    )
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"email": "new.email@example.com"}})
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    uuid: str
    email: str
    role: str

class UserListResponse(BaseModel):
    users: list[UserResponse]

class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    refresh_token: str
    expires_in: int
    user_uuid: str

class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"refresh_token": "eyJhbGciOi..."}})
    refresh_token: str

class RoleUpdate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"role": "ADMIN"}})
    role: UserRole
