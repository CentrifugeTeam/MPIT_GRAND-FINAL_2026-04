from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PLATFORM_DATABASE_URL: str = (
        "postgresql://postgres:postgres@postgres-db:5432/postgres-db"
    )
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = "admin123"
    RABBITMQ_PORT: int = 5672
    DISPATCH_INTERVAL_SECONDS: int = 60
    REPORT_TASK_INTERNAL_TOKEN: str = "dev-report-internal-token"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
