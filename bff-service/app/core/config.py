from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # JWT настройки
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"

    # Локальный режим
    BACKEND_LOCAL: bool = False

    # Сервисы
    AUTH_SERVICE_URL: str = "http://auth-service:8002"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8007"
    FILES_SERVICE_URL: str = "http://files-service:8006"

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
