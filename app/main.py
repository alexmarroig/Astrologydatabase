"""
Astro Platform — FastAPI application entry point.

Startup sequence:
  1. Load settings (from .env)
  2. Configure CORS, exception handlers, middleware
  3. Mount API routers
  4. Expose a lifespan hook for future startup/shutdown work

Database schema creation is handled via Alembic migrations.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import AstroPlatformError, astro_exception_handler
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Schema management is intentionally delegated to Alembic.
    This hook remains in place for future startup/shutdown concerns:
      - worker bootstrap
      - cache warm-up
      - admin panel integration
      - connection/resource cleanup
    """
    yield

    # Future: await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Professional astrological interpretation system. "
            "Implements the formal ontology defined in the architecture document."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ───────────────────────────────────────────────────
    app.add_exception_handler(AstroPlatformError, astro_exception_handler)

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(api_v1_router)

    # ── Health & Meta ────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health_check() -> JSONResponse:
        return JSONResponse(
            content={
                "status": "ok",
                "app": settings.app_name,
                "version": settings.app_version,
                "environment": settings.app_env,
            }
        )

    @app.get("/", tags=["Health"], include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "message": f"Welcome to {settings.app_name}",
                "docs": "/docs",
                "health": "/health",
            }
        )

    return app


app = create_app()
