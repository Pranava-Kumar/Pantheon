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

from db.session import init_db
from api.routes import router

app = FastAPI(
    title="Project Pantheon",
    description="MMCI Signal Intelligence API — Real-time market signals powered by multi-model consensus.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for development; lock down in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "name": "Project Pantheon",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
