from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANALYTICS_DATABASE_URL: str = (
        "postgresql://postgres:postgres@postgres-db:5432/postgres-db"
    )
    # «Наша БД»: метаданные задач NL→SQL (можно совпадать с ANALYTICS_DATABASE_URL)
    PLATFORM_DATABASE_URL: str = (
        "postgresql://postgres:postgres@postgres-db:5432/postgres-db"
    )

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    RABBITMQ_PORT: int = 5672

    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    SCHEMA_CACHE_TTL_SECONDS: int = 86400
    # Ежедневное обновление кэша схемы (час UTC, 0–23)
    SCHEMA_CRON_HOUR: int = 3
    QUERY_TIMEOUT_MS: int = 30000

    # Empty = любые таблицы из текущей схемы public с разрешёнными приставками в guard
    ALLOWED_TABLES: Optional[str] = None  # comma-separated list

    # Источники данных (SELECT): таблица analytics_data_sources; при пустой БД — сид из env
    DEFAULT_ANALYTICS_SOURCE_KEY: str = "main-db"
    # JSON: [{"key":"main-db","display_name":"…","database_url":"postgresql://…"}]
    ANALYTICS_SOURCES_JSON: str = ""
    # Альтернатива JSON: main-db|postgresql://…||other|postgresql://…
    ANALYTICS_SOURCES_INLINE: str = ""
    # Если непусто — POST/PATCH/DELETE/default требуют заголовок X-Analytics-Sources-Write-Token
    ANALYTICS_SOURCES_WRITE_TOKEN: str = ""

    # Синхронизация сообщений NL-чата из nl-orchestrator-worker (заголовок X-Chat-Sync-Token)
    INTERNAL_NL_CHAT_SYNC_TOKEN: str = ""

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
