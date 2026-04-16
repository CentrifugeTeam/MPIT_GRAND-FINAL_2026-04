from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@postgres-files:5432/files_db"

    # Storage
    STORAGE_PATH: str = "/app/storage"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Upload policy:
    # - allow almost any extension
    # - block a small denylist of obviously risky executable/script types
    DISALLOWED_EXTENSIONS: set[str] = {
        ".app",
        ".bat",
        ".cmd",
        ".com",
        ".cpl",
        ".dmg",
        ".exe",
        ".gadget",
        ".hta",
        ".jar",
        ".js",
        ".jse",
        ".msi",
        ".msp",
        ".pif",
        ".ps1",
        ".psm1",
        ".reg",
        ".scr",
        ".sh",
        ".vb",
        ".vbe",
        ".vbs",
        ".wsf",
    }

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()

