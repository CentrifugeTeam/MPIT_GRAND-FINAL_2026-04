from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, files, notification

app = FastAPI(
    title="BFF Service",
    description="Backend for Frontend Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
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


@app.get("/")
async def root():
    return {"message": "BFF Service is running"}
