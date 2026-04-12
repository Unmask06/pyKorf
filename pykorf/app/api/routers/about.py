"""About API: /api/about."""

from __future__ import annotations

from fastapi import APIRouter

from pykorf.app.api.schemas import AboutResponse

router = APIRouter()

_RELEASE_DATE = "2026-03-29"


@router.get("/", response_model=AboutResponse)
async def about():
    """Return version and release info."""
    from pykorf import __version__

    return AboutResponse(version=__version__, release_date=_RELEASE_DATE)
