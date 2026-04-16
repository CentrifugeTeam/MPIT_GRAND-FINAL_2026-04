from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import notifications
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Email Notification Service with RabbitMQ",
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

app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/")
async def root():
    return {"message": "Notification Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
