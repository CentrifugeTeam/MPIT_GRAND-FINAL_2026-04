from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANALYTICS_DATABASE_URL: str = (
        "postgresql://postgres:postgres@postgres-db:5432/postgres-db"
    )
    PLATFORM_DATABASE_URL: str = (
        "postgresql://postgres:postgres@postgres-db:5432/postgres-db"
    )
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    QUERY_MAX_ROWS: int = 500
    QUERY_TIMEOUT_MS: int = 30000
    ALLOWED_TABLES: str | None = None

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    RABBITMQ_PORT: int = 5672

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
