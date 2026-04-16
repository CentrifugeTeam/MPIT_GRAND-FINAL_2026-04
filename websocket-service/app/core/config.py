from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # JWT настройки
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"

    # WebSocket настройки
    WEBSOCKET_PORT: int = 8008

    # RabbitMQ настройки (для интеграции с notification service)
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    RABBITMQ_PORT: int = 5672

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
