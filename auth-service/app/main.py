from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, roles, users
from app.database import Base, engine
from app.db_migrate import ensure_roles_and_user_column
from app.models import RefreshToken, RoleDefinition, User  # noqa: F401

ensure_roles_and_user_column(engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth Service",
    description="Аутентификация, пользователи и справочник ролей (JWT, refresh).",
    version="1.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "auth", "description": "Вход, refresh, выход."},
        {"name": "users", "description": "CRUD пользователей и смена роли."},
        {"name": "roles", "description": "Справочник ролей (ADMIN)."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])


@app.get("/")
async def root():
    return {"message": "Auth Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
