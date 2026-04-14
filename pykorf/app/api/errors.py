"""FastAPI exception handlers."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from pykorf.app.exceptions import UseCaseError
from pykorf.core.exceptions import KorfError


async def use_case_error_handler(request: Request, exc: UseCaseError) -> JSONResponse:
    """Handle UseCaseError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def korf_error_handler(request: Request, exc: KorfError) -> JSONResponse:
    """Handle core KorfError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    from pykorf.core.log import get_logger

    get_logger(__name__).error("unhandled_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
