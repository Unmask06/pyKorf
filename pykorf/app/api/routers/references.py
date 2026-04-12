"""References API: /api/references/*."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from pykorf.app.api import session_state as _sess
from pykorf.app.api.deps import require_model
from pykorf.app.api.schemas import (
    AddReferenceRequest,
    DeleteReferenceRequest,
    OkResponse,
    ReferencesStoreSchema,
    SaveAllReferencesRequest,
    ShortcutsResponse,
    UpdateReferenceRequest,
)
from pykorf.core.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _load_refs():
    from pykorf.app.operation.project.references import ReferencesStore

    kdf_path = _sess.get_kdf_path_sync()
    if kdf_path is None:
        return ReferencesStore()
    return ReferencesStore.load(kdf_path)


@router.get("/", response_model=ReferencesStoreSchema)
async def get_references():
    """Get references store for the active model."""
    await require_model()

    store = _load_refs()

    return ReferencesStoreSchema(
        basis=store.basis,
        remarks=store.remarks,
        hold=store.hold,
        references=[
            {
                "id": r.id,
                "name": r.name,
                "link": r.link,
                "description": r.description,
                "category": r.category,
            }
            for r in store.references
        ],
    )


@router.post("/save-all", response_model=OkResponse)
async def save_all(req: SaveAllReferencesRequest) -> OkResponse:
    """Save basis, remarks, and hold items."""
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        raise HTTPException(status_code=412, detail="No model loaded.")
    store = _load_refs()
    store.basis = req.basis
    store.remarks = req.remarks
    store.hold = req.hold
    store.save(kdf_path)
    return OkResponse(success=True)


@router.post("/add", response_model=OkResponse)
async def add_reference(req: AddReferenceRequest) -> OkResponse:
    """Add or update a reference entry."""
    await require_model()
    from pykorf.app.operation.project.references import Reference

    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        raise HTTPException(status_code=412, detail="No model loaded.")
    store = _load_refs()

    if req.name and req.link:
        if req.edit_id:
            store.update(
                req.edit_id,
                name=req.name,
                link=req.link,
                description=req.description,
                category=req.category,
            )
        else:
            store.add(
                Reference.new(
                    name=req.name, link=req.link, description=req.description, category=req.category
                )
            )
        store.save(kdf_path)
        store.create_shortcuts(kdf_path)

    return OkResponse(success=True)


@router.post("/update", response_model=OkResponse)
async def update_reference(req: UpdateReferenceRequest) -> OkResponse:
    """Update an existing reference by ID."""
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        raise HTTPException(status_code=412, detail="No model loaded.")
    store = _load_refs()
    if req.ref_id:
        store.update(
            req.ref_id,
            name=req.name,
            link=req.link,
            description=req.description,
            category=req.category,
        )
        store.save(kdf_path)
        store.create_shortcuts(kdf_path)
    return OkResponse(success=True)


@router.post("/delete", response_model=OkResponse)
async def delete_reference(req: DeleteReferenceRequest) -> OkResponse:
    """Delete a reference by ID."""
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    if not kdf_path:
        raise HTTPException(status_code=412, detail="No model loaded.")
    store = _load_refs()
    if req.ref_id:
        store.delete(req.ref_id)
        store.save(kdf_path)
    return OkResponse(success=True)


@router.post("/shortcuts", response_model=ShortcutsResponse)
async def create_shortcuts():
    """Create .url shortcut files in the reference/ folder."""
    await require_model()
    kdf_path = await _sess.get_kdf_path()
    store = _load_refs()

    try:
        count, ref_dir = store.create_shortcuts(kdf_path)
        return ShortcutsResponse(count=count, path=str(ref_dir))
    except Exception as exc:
        return ShortcutsResponse(error=str(exc))
