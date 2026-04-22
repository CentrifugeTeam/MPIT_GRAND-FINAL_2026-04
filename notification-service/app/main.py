from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import notifications
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Уведомления и настройки; доставка email через RabbitMQ.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "notifications", "description": "CRUD уведомлений, настройки, постановка в очередь."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
