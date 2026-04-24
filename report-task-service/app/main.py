from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tasks import router as tasks_router
from app.api.templates import router as templates_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import init_tables
    from app.services.scheduler import start_scheduler, stop_scheduler
    from app.services.template_seed_jobs import start_background_template_seed

    init_tables()
    start_scheduler()
    start_background_template_seed()
    yield
    stop_scheduler()


app = FastAPI(
    title="Report Task Service",
    description="Планировщик отчётных задач и история прогонов (NL→SQL отчёты).",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "report-tasks", "description": "Задачи и прогоны; заголовок X-User-Id обязателен."},
        {
            "name": "report-task-templates",
            "description": "Шаблоны отчётных задач (пресеты расписания и текста); X-User-Id обязателен.",
        },
        {
            "name": "internal",
            "description": "Внутренние вызовы (X-Report-Internal-Token): результат прогона, bulk шаблоны.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router, prefix="/api/reports", tags=["report-tasks"])
app.include_router(templates_router, prefix="/api/reports", tags=["report-task-templates"])


@app.get("/health")
async def health():
    return {"status": "ok"}
