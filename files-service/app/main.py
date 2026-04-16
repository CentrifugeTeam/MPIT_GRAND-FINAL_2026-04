from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api import files
from app.database import engine, Base
from app.core.config import get_settings
from pathlib import Path

settings = get_settings()

# Создать директорию для хранилища
storage_path = Path(settings.STORAGE_PATH)
storage_path.mkdir(parents=True, exist_ok=True)

# Лёгкая миграция для dev: убрать legacy-колонки, если они остались в БД
with engine.begin() as conn:
    conn.execute(
        text(
            "ALTER TABLE files DROP COLUMN IF EXISTS project_id"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE files DROP COLUMN IF EXISTS file_type"
        )
    )
    # enum тип мог остаться от старой схемы
    conn.execute(
        text(
            "DO $$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'filetype') THEN "
            "DROP TYPE filetype; "
            "END IF; "
            "END $$;"
        )
    )

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Files Service",
    description="File Storage and Management Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router, prefix="/files", tags=["files"])

@app.get("/")
async def root():
    return {"message": "Files Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

