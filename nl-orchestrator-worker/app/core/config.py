from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    RABBITMQ_PORT: int = 5672

    CHAT_MAX_HISTORY_MESSAGES: int = 20
    CHAT_SQL_MAX_ROWS: int = 10000

    ANALYTICS_SERVICE_URL: str = ""
    AUTH_SERVICE_URL: str = "http://auth-service:8002"
    INTERNAL_NL_CHAT_SYNC_TOKEN: str = ""
    NOTIFICATION_SERVICE_URL: str = ""
    REPORT_TASK_SERVICE_URL: str = "http://report-task-service:8010"
    REPORT_TASK_INTERNAL_TOKEN: str = "dev-report-internal-token"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
