from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserListResponse,
    RoleUpdate,
    TokenResponse,
    RefreshTokenRequest,
    UserCreatedResponse,
    LogoutResponse,
)
from app.services.auth_service import AuthService
from app.core.config import get_settings

router = APIRouter()
security = HTTPBearer()
settings = get_settings()

auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Получить текущего пользователя из JWT токена."""

    if settings.BACKEND_LOCAL:
        return {
            "email": "local@user.com",
            "role": "ADMIN",
            "uuid": "00000000-0000-0000-0000-000000000001",
        }

    try:
        payload = auth_service.decode_token(credentials.credentials)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Текущий пользователь",
    description="Данные из auth-service по email из JWT.",
    responses={401: {"description": "Нет или просрочен JWT"}, 404: {"description": "Пользователь не найден"}},
)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    if settings.BACKEND_LOCAL:
        return UserResponse(
            uuid=current_user["uuid"],
            email=current_user["email"],
            role=current_user["role"],
        )

    try:
        user = await auth_service.get_user_by_email(current_user["email"])
        return UserResponse(
            uuid=str(user["uuid"]),
            email=user["email"],
            role=str(user.get("role", "USER")),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.get(
    "/user/{user_id}",
    response_model=UserResponse,
    summary="Пользователь по UUID",
    description="Доступно при валидном JWT.",
    responses={401: {"description": "Нет JWT"}, 404: {"description": "Не найден"}},
)
async def get_user_by_id(user_id: str, current_user: dict = Depends(get_current_user)):
    try:
        user = await auth_service.get_user_by_id(user_id)
        return UserResponse(
            uuid=str(user["uuid"]),
            email=user["email"],
            role=str(user.get("role", "USER")),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Список всех пользователей",
    description="Только роль ADMIN.",
    responses={401: {"description": "Нет JWT"}, 403: {"description": "Не ADMIN"}},
)
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    try:
        response = await auth_service.get_all_users()
        users = response.get("users", [])
        return UserListResponse(users=users)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users",
        )


@router.post(
    "/me",
    response_model=UserResponse,
    summary="Обновить профиль текущего пользователя",
    description="Частичное обновление email (и опционально роли, если разрешено auth).",
    responses={400: {"description": "Ошибка валидации или auth-service"}},
)
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        updated_user = await auth_service.update_user(
            current_user["email"],
            user_update.model_dump(exclude_unset=True),
        )
        return UserResponse(
            uuid=str(updated_user["uuid"]),
            email=updated_user["email"],
            role=str(updated_user.get("role", "USER")),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user",
        )


@router.post(
    "/create",
    response_model=UserCreatedResponse,
    summary="Регистрация пользователя (публично)",
    description="Прокси в auth-service; пароли должны совпадать.",
    responses={400: {"description": "Пароли не совпадают или ошибка auth-service"}},
)
async def create_user(user_data: UserCreate):
    try:
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )

        user = await auth_service.create_user(user_data.model_dump())
        return UserCreatedResponse(
            message="User created successfully",
            uuid=str(user["uuid"]),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход",
    description="Выдача access и refresh токенов.",
    responses={401: {"description": "Неверные учётные данные"}},
)
async def login_user(user_credentials: UserLogin):
    try:
        result = await auth_service.authenticate_user(
            user_credentials.email,
            user_credentials.password,
        )
        return TokenResponse(**result)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновить access-токен",
    description="По refresh из тела запроса.",
    responses={401: {"description": "Невалидный или просроченный refresh"}},
)
async def refresh_token(token_request: RefreshTokenRequest):
    try:
        result = await auth_service.refresh_access_token(token_request.refresh_token)
        return TokenResponse(**result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Выход (отзыв refresh на стороне auth)",
    description="Прокси POST в auth-service /auth/logout.",
    responses={400: {"description": "Не удалось выполнить logout"}},
)
async def logout(token_request: RefreshTokenRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/logout",
                json={"refresh_token": token_request.refresh_token},
            )
            response.raise_for_status()
            return LogoutResponse(message="Successfully logged out")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout",
        )


@router.put(
    "/user/{user_uuid}/role",
    response_model=TokenResponse,
    summary="Сменить роль пользователя",
    description="Прокси в auth-service; возвращаются новые токены.",
    responses={404: {"description": "Пользователь не найден"}, 500: {"description": "Ошибка auth-service"}},
)
async def update_user_role(
    user_uuid: str,
    role_data: RoleUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        user = await auth_service.update_user_role(user_uuid, role_data.role)
        return TokenResponse(**user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
