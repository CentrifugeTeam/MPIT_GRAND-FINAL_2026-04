from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from app.database import get_db
from app.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserListResponse,
    RoleUpdate,
    TokenResponse,
    MessageResponse,
)
from app.crud import user_crud
from app.utils.auth import verify_token, create_access_token, create_refresh_token
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

def get_current_user(token: str = Depends(verify_token)):
    """Получить текущего пользователя из токена"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return token

def require_admin(current_user: dict = Depends(get_current_user)):
    """Проверить права администратора"""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.post("/", response_model=UserResponse, summary="Создать пользователя", description="Публичная регистрация; email уникален.")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = user_crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        db_user = user_crud.create_user(db, user)
        return UserResponse.model_validate(db_user, from_attributes=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_uuid}", response_model=UserResponse, summary="Пользователь по UUID")
async def get_user(user_uuid: str, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_uuid(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user, from_attributes=True)

@router.get("/email/{email}", response_model=UserResponse, summary="Пользователь по email")
async def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user, from_attributes=True)

@router.get("/", response_model=UserListResponse, summary="Список пользователей", description="Пагинация skip/limit.")
async def get_all_users(
    skip: int = Query(0, ge=0, description="Пропустить записей с начала"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей"),
    db: Session = Depends(get_db),
):
    users = user_crud.get_all_users(db, skip=skip, limit=limit)
    return UserListResponse(
        users=[UserResponse.model_validate(user, from_attributes=True) for user in users]
    )

@router.put(
    "/{user_uuid}",
    response_model=UserResponse,
    summary="Обновить пользователя по UUID",
    description="Только ADMIN.",
)
async def update_user(
    user_uuid: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user = user_crud.update_user(db, user_uuid, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user, from_attributes=True)

@router.put(
    "/email/{email}",
    response_model=UserResponse,
    summary="Обновить пользователя по email",
    description="Свой email или ADMIN.",
)
async def update_user_by_email(
    email: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("email") != email and current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user = user_crud.update_user_by_email(db, email, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user, from_attributes=True)

@router.post("/{user_uuid}/verify", response_model=MessageResponse, summary="Подтвердить email пользователя")
async def verify_user(user_uuid: str, db: Session = Depends(get_db)):
    user = user_crud.verify_user(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return MessageResponse(message="User verified successfully")


@router.put(
    "/{user_uuid}/role",
    response_model=TokenResponse,
    summary="Сменить роль",
    description="Новая пара access+refresh.",
)
async def update_user_role(
    user_uuid: str,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
):
    try:
        from uuid import UUID
        UUID(user_uuid)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = user_crud.update_user_role(db, user_uuid, role_update.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "email": user.email,
        "role": str(user.role),
        "uuid": str(user.uuid)
    }

    access_token = create_access_token(token_data, access_token_expires)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_uuid=str(user.uuid)
    )
