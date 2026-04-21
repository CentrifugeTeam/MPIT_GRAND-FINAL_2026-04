from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, files, notification, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.analytics_mq_consumer import start_consumer, stop_consumer
    from app.services.chat_mq import chat_bus

    await chat_bus.start()
    start_consumer()
    yield
    await stop_consumer()
    await chat_bus.stop()


app = FastAPI(
    title="BFF Service",
    description="Backend for Frontend Service",
    version="1.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(notification.router, prefix="/api/notification", tags=["notification"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(websocket.router, prefix="/api/websocket", tags=["websocket"])


@app.get("/")
async def root():
    return {"message": "BFF Service is running"}
