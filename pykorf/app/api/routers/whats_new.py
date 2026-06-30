"""What's New API: /api/whats-new/*."""

from __future__ import annotations

from fastapi import APIRouter

from pykorf.app.api.schemas import (
    EmptyRequest,
    WhatsNewResponse,
    WhatsNewSeenResponse,
)
from pykorf.app.whats_new import get_whats_new, mark_whats_new_seen

router = APIRouter()


@router.get("", response_model=WhatsNewResponse, operation_id="getWhatsNew")
async def api_get_whats_new() -> WhatsNewResponse:
    """Return the changelog section for the current app version.

    The response always includes the current version and date. The
    ``has_unseen`` flag indicates whether the user has not yet acknowledged
    this version — the frontend uses it to decide whether to auto-pop the
    modal on startup. Empty ``sections`` means there is no changelog entry
    for the current version (e.g. dev builds) and the modal should not show.
    """
    data = get_whats_new()
    return WhatsNewResponse(
        version=data["version"],
        date=data["date"],
        sections=data["sections"],
        has_unseen=data["has_unseen"],
    )


@router.post(
    "/seen",
    response_model=WhatsNewSeenResponse,
    operation_id="markWhatsNewSeen",
)
async def api_mark_whats_new_seen(_: EmptyRequest) -> WhatsNewSeenResponse:
    """Record that the user has seen the "What's New" modal for the current version."""
    version = mark_whats_new_seen()
    return WhatsNewSeenResponse(status="ok", version=version)
