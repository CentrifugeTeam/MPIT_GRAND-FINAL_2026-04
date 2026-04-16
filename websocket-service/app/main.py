from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import websocket

app = FastAPI(
    title="WebSocket Service",
    description="Real-time WebSocket Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(websocket.router, tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "WebSocket Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
