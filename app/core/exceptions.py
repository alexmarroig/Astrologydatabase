"""
Domain exceptions and HTTP error handlers for the Astro Platform.

Hierarchy:
  AstroPlatformError (base)
  ├── NotFoundError          → 404
  ├── ConflictError          → 409
  ├── ValidationError        → 422
  ├── EditorialError         → 422 (editorial workflow violations)
  └── ForbiddenError         → 403
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AstroPlatformError(Exception):
    """Base exception for all domain errors."""
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AstroPlatformError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictError(AstroPlatformError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists"


class DomainValidationError(AstroPlatformError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error"


class EditorialWorkflowError(AstroPlatformError):
    """Raised when an editorial workflow transition is invalid."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Invalid editorial workflow transition"


class ForbiddenError(AstroPlatformError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Access forbidden"


# ── FastAPI exception handlers ────────────────────────────────────────────────

async def astro_exception_handler(
    request: Request, exc: AstroPlatformError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_type": type(exc).__name__},
    )
