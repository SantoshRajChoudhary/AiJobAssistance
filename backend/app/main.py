"""
Hidani Tech - AI Job Chat Assistant
FastAPI Main Application.
"""

import sys
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
)
from app.services.storage_service import storage_service
from app.api.routes import health, resume, chat, jobs, applications, job_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_job_assistant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event: verifies data availability and startup state."""
    logger.info("Initializing Hidani AI Job Assistant Backend...")
    total_jobs = len(storage_service.load_jobs())
    logger.info(f"Storage ready: {total_jobs} real jobs indexed in data/jobs.json.")
    yield
    logger.info("Shutting down Hidani AI Job Assistant Backend.")


app = FastAPI(
    title="Hidani Tech AI Job Assistant",
    description="Intelligent multi-agent job matching and application assistant with real scraped job data.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
# CORS is configured specifically for designated frontend origins as required.
_cors_list = settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins]
_is_wildcard = "*" in _cors_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_list,
    allow_credentials=not _is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ───────────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Transforms FastAPI Pydantic validation errors into consistent structured JSON."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload.",
                "details": exc.errors(),
            }
        },
    )


if not settings.debug:
    app.add_exception_handler(Exception, generic_exception_handler)

# ─── Include Routers ──────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(resume.router)
app.include_router(chat.router)
app.include_router(job_stats.router)  # Must be before jobs.router (avoids /stats vs /{job_id} conflict)
app.include_router(jobs.router)
app.include_router(applications.router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "Hidani Tech AI Job Assistant",
        "health": "/api/health",
        "docs": "/docs",
    }
