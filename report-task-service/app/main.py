from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import init_tables
    from app.services.scheduler import start_scheduler, stop_scheduler

    init_tables()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Report Task Service",
    description="Task scheduler + report run history for analytics reports.",
    version="1.0.0",
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

app.include_router(tasks_router, prefix="/api/reports", tags=["report-tasks"])


@app.get("/health")
async def health():
    return {"status": "ok"}
