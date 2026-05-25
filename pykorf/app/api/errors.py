"""FastAPI exception handlers."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def _json_error_handler(status_code: int):
    """Factory for simple JSON error handlers."""

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc)},
        )

    return handler


use_case_error_handler = _json_error_handler(400)
korf_error_handler = _json_error_handler(400)


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    from pykorf.core.log import get_logger

    get_logger(__name__).error("unhandled_error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
