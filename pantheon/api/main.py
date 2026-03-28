"""
Project Pantheon — FastAPI Application Entry Point

Run locally:  uvicorn api.main:app --reload --port 8080
Production:   uvicorn api.main:app --host 0.0.0.0 --port $PORT
"""

import sys
from pathlib import Path

# Ensure pantheon package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from pantheon.config.settings import settings
from pantheon.db.session import init_db
from pantheon.db.redis_client import init_redis, close_redis
from pantheon.api.routes import router
from pantheon.api.rate_limiters import global_rate_limiter, auth_rate_limiter, trigger_rate_limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    await init_redis()
    # Start rate limiter cleanup tasks
    await global_rate_limiter.start_cleanup_task()
    await auth_rate_limiter.start_cleanup_task()
    await trigger_rate_limiter.start_cleanup_task()
    yield
    # Shutdown
    await close_redis()
    # Stop rate limiter cleanup tasks
    await global_rate_limiter.stop_cleanup_task()
    await auth_rate_limiter.stop_cleanup_task()
    await trigger_rate_limiter.stop_cleanup_task()

app = FastAPI(
    title="Project Pantheon",
    description="MMCI Signal Intelligence API — Real-time market signals powered by multi-model consensus.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Restrict CORS origins based on settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")

def root():
    return {
        "name": "Project Pantheon",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
