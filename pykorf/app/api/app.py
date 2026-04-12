"""FastAPI application factory and server runner."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pykorf.app.update_check import prefetch as _prefetch

_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app with all routers registered.
    """
    app = FastAPI(title="pyKorf", version="0.18.0")

    # --- Register routers ---
    from pykorf.app.api.routers import (
        about,
        browse,
        data,
        doc_register,
        model,
        preferences,
        references,
        report,
        session,
        settings,
    )

    app.include_router(session.router, prefix="/api/session", tags=["session"])
    app.include_router(model.router, prefix="/api/model", tags=["model"])
    app.include_router(data.router, prefix="/api/data", tags=["data"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
    app.include_router(report.router, prefix="/api/report", tags=["report"])
    app.include_router(browse.router, prefix="/api/browse", tags=["browse"])
    app.include_router(
        doc_register.router, prefix="/api/doc-register", tags=["doc-register"]
    )
    app.include_router(
        preferences.router, prefix="/api/preferences", tags=["preferences"]
    )
    app.include_router(
        references.router, prefix="/api/references", tags=["references"]
    )
    app.include_router(about.router, prefix="/api/about", tags=["about"])

    # --- Register exception handlers ---
    from pykorf.app.api.errors import (
        generic_error_handler,
        korf_error_handler,
        use_case_error_handler,
    )
    from pykorf.app.exceptions import UseCaseError
    from pykorf.core.exceptions import KorfError

    app.add_exception_handler(UseCaseError, use_case_error_handler)
    app.add_exception_handler(KorfError, korf_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # --- Shutdown endpoint ---
    @app.post("/api/session/shutdown", include_in_schema=False)
    async def shutdown_server(request: Request) -> JSONResponse:
        """Stop the uvicorn server (localhost only)."""
        if request.client and request.client.host not in ("127.0.0.1", "::1"):
            return JSONResponse({"error": "Forbidden"}, status_code=403)

        import os
        import signal

        from pykorf.core.log import get_logger

        get_logger(__name__).info("shutdown_requested")
        # Graceful shutdown: signal uvicorn to stop
        os.kill(os.getpid(), signal.SIGINT)
        return JSONResponse({"status": "shutting_down"})

    # --- Prefetch update check ---
    _prefetch()

    # --- Serve Vue SPA static files ---
    if _FRONTEND_DIST.is_dir():
        # Mount assets subdirectory
        assets_dir = _FRONTEND_DIST / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # Catch-all: serve index.html for SPA client-side routing
        @app.get("/{path:path}", include_in_schema=False)
        async def serve_spa(path: str) -> FileResponse:
            """Serve Vue SPA — return index.html for all non-API routes."""
            # Try to serve a real file first (e.g. favicon.ico)
            file_path = _FRONTEND_DIST / path
            if path and file_path.is_file():
                return FileResponse(str(file_path))
            # Fall back to index.html for SPA routing
            index = _FRONTEND_DIST / "index.html"
            if index.is_file():
                return FileResponse(str(index))
            return FileResponse(str(index))

    return app


def run_server(port: int = 8000, debug: bool = True) -> None:
    """Start the uvicorn server and open the browser.

    Args:
        port: TCP port to listen on (default 8000).
        debug: When True, enable auto-reload and DEBUG log level.
    """
    from pykorf.app.api._logging import setup_console_logging

    setup_console_logging(debug=debug)

    url = f"http://localhost:{port}"
    print(f"\n  pyKorf Web UI -> {url}\n  Press Ctrl+C to stop.\n")

    # Open browser after a short delay
    threading.Timer(0.8, webbrowser.open, args=[url]).start()

    import uvicorn

    uvicorn.run(
        "pykorf.app.api.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=port,
        reload=debug,
        log_level="debug" if debug else "warning",
    )
