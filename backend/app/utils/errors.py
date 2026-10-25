"""
Custom exceptions and structured error handlers for the FastAPI application.
"""

from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception with status code and error details."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class InvalidInputError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_INPUT",
            details=details,
        )


class FileTooLargeError(AppException):
    def __init__(self, message: str = "File size exceeds the 5 MB limit."):
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
        )


class JobNotFoundError(AppException):
    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job with ID '{job_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="JOB_NOT_FOUND",
            details={"job_id": job_id},
        )


class DuplicateApplicationError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_APPLICATION",
            details=details,
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again shortly."):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
        )


class UpstreamServiceError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="UPSTREAM_SERVICE_ERROR",
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Format custom app exceptions into structured JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler ensuring internal stack traces and secrets are not leaked."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": str(exc) if getattr(request.app.state, "debug", False) else None,
            }
        },
    )
