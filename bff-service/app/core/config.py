from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT настройки
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"

    # Локальный режим
    BACKEND_LOCAL: bool = False

    # Сервисы
    AUTH_SERVICE_URL: str = "http://auth-service:8002"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8007"
    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8009"
    # Если фронт не передал analytics_source_key в WS chat_message — подставить этот ключ (как в analytics-service).
    DEFAULT_ANALYTICS_SOURCE_KEY: str = "main-db"
    # Ключи источников (через запятую), запрещённые для NL chat_message — заменяются на DEFAULT_ANALYTICS_SOURCE_KEY.
    NL_CHAT_BLOCKED_SOURCE_KEYS: str = "postgres-main"
    # Проксируется в analytics-service при CRUD /api/analytics/data-sources (ADMIN в BFF)
    ANALYTICS_SOURCES_WRITE_TOKEN: str = ""

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    RABBITMQ_PORT: int = 5672

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
