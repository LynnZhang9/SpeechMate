# host/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from api.config import router as config_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure config directory exists
    config_dir = os.path.expanduser("~/.speechmate")
    os.makedirs(config_dir, exist_ok=True)
    yield
    # Shutdown: cleanup if needed

app = FastAPI(
    title="SpeechMate Host",
    description="Voice recognition and translation assistant server",
    version="0.1.0",
    lifespan=lifespan
)

# Include API routers
app.include_router(config_router)

# Mount static files for Web Admin
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"name": "SpeechMate Host", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
