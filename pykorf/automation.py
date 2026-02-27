"""KorfApp – pywinauto-based automation wrapper for KORF.

This module provides a safe, connect-only interface to a **running** KORF
instance.  It **never** launches a new process, preserving your trial-use
count.

Usage (typical notebook workflow)::

    from pykorf.automation import KorfApp

    app = KorfApp.connect()  # attach to the already-open KORF
    app.reload_model("Pumpcases.kdf")
    app.run_hydraulics()
    app.wait_for_run(timeout=30)
    app.save_model()
    app.disconnect()

Convenience function::

    from pykorf.automation import open_ui

    open_ui("library/Pumpcases.kdf")  # opens in the running KORF instance

All methods are safe to call in succession; the window handle is
re-acquired before each action to stay robust against dialog changes.
"""

from __future__ import annotations

import time
from pathlib import Path

from pykorf.exceptions import AutomationError

try:
    from pywinauto.application import Application
    from pywinauto.timings import TimeoutError as WinTimeout

    _PYWINAUTO_AVAILABLE = True
except ImportError:
    _PYWINAUTO_AVAILABLE = False


KORF_PATH_DEFAULT = r"C:\Program Files (x86)\Korf 36\Korf_36.exe"


class KorfApp:
    """Thin wrapper around a running KORF instance.

    Parameters
    ----------
    korf_path:
        Path to the KORF executable.  Used only to *connect* to the
        process, not to launch it.
    """

    def __init__(self, korf_path: str = KORF_PATH_DEFAULT):
        if not _PYWINAUTO_AVAILABLE:
            raise AutomationError(
                "pywinauto is not installed. Install it with: pip install pywinauto"
            )
        self._korf_path = korf_path
        self._app: Application | None = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @classmethod
    def connect(cls, korf_path: str = KORF_PATH_DEFAULT) -> KorfApp:
        """Connect to the currently running KORF process.

        This is the recommended entry-point.  KORF must already be open.

        Raises:
        ------
        AutomationError
            If KORF is not running or cannot be found.
        """
        instance = cls(korf_path)
        instance._connect()
        return instance

    def _connect(self) -> None:
        try:
            self._app = Application(backend="win32").connect(path=self._korf_path)
        except Exception as exc:
            raise AutomationError(
                f"Cannot connect to KORF at '{self._korf_path}'. "
                f"Is KORF open?  Error: {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Release the connection handle."""
        self._app = None

    def _require_connected(self) -> None:
        if self._app is None:
            raise AutomationError("Not connected to KORF. Call connect() first.")

    # ------------------------------------------------------------------
    # Window helpers
    # ------------------------------------------------------------------

    def _main_window(self):
        """Re-acquire the top-level KORF window (safest approach)."""
        self._require_connected()
        dlg = self._app.top_window()
        dlg.set_focus()
        return dlg

    @property
    def window_title(self) -> str:
        """Current KORF window title."""
        return self._main_window().window_text()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def reload_model(self, model_path: str | Path) -> None:
        """Open / reload *model_path* in the existing KORF window using Ctrl+O.

        This does **not** launch a new KORF process; it opens a file inside
        the running instance.

        Parameters
        ----------
        model_path:
            Absolute or relative path to the .kdf file.
        """
        abs_path = str(Path(model_path).resolve())
        main = self._main_window()

        print(f"[KorfApp] Sending Ctrl+O to reload: {abs_path}")
        main.type_keys("^o")
        time.sleep(1.0)

        try:
            open_dlg = self._app.window(title_re=".*Open.*")
            open_dlg.wait("visible", timeout=10)
            open_dlg.Edit.set_edit_text(abs_path)
            open_dlg.type_keys("{ENTER}")
            time.sleep(2.0)
        except Exception as exc:
            raise AutomationError(
                f"Open dialog did not appear or could not be filled: {exc}"
            ) from exc

        # Re-acquire main window after reload
        _ = self._main_window()
        print(f"[KorfApp] Model reloaded.  Window: '{self.window_title}'")

    def save_model(self) -> None:
        """Save the current model with Ctrl+S."""
        main = self._main_window()
        print("[KorfApp] Saving model (Ctrl+S)…")
        main.type_keys("^s")
        time.sleep(1.0)
        print("[KorfApp] Save command sent.")

    # ------------------------------------------------------------------
    # Hydraulics menu
    # ------------------------------------------------------------------

    def run_hydraulics(self) -> None:
        """Click ``Hydraulics → Hydraulics → Run`` in the menu bar.

        Confirmed menu path from live inspection:
        ``Hy&draulics → &Hydraulics → &Run``
        (pywinauto strips the & accelerator characters when matching).
        """
        main = self._main_window()
        time.sleep(0.3)
        print("[KorfApp] Triggering: Hydraulics → Hydraulics → Run …")
        try:
            main.menu_select("Hydraulics -> Hydraulics -> Run")
            print("[KorfApp] Run command sent.")
        except Exception as exc:
            raise AutomationError(f"Could not navigate Hydraulics menu: {exc}") from exc

    def stop_hydraulics(self) -> None:
        """Click ``Hydraulics → Hydraulics → Stop``."""
        main = self._main_window()
        main.menu_select("Hydraulics -> Hydraulics -> Stop")

    def resume_hydraulics(self) -> None:
        """Click ``Hydraulics → Hydraulics → Resume``."""
        main = self._main_window()
        main.menu_select("Hydraulics -> Hydraulics -> Resume")

    # ------------------------------------------------------------------
    # Post-run dialog handling
    # ------------------------------------------------------------------

    def wait_for_run(self, timeout: float = 30.0) -> bool:
        """Wait for the KORF Runlog dialog to appear and dismiss it.

        Parameters
        ----------
        timeout:
            Maximum seconds to wait.

        Returns:
        -------
        bool
            *True* if the dialog was found and dismissed, *False* if it
            did not appear within *timeout*.
        """
        self._require_connected()
        print(f"[KorfApp] Waiting for Runlog (timeout={timeout}s)…")
        try:
            runlog = self._app.window(title_re=".*[Rr]unlog.*")
            runlog.wait("visible", timeout=timeout)
            print(f"[KorfApp] Runlog: '{runlog.window_text()}' – clicking OK.")
            runlog.OK.click()
            print("[KorfApp] Runlog dismissed.")
            return True
        except Exception:
            print("[KorfApp] Runlog did not appear (run may have completed instantly).")
            return False

    # ------------------------------------------------------------------
    # Full automation cycle
    # ------------------------------------------------------------------

    def run_cycle(
        self,
        model_path: str | Path,
        timeout: float = 30.0,
    ) -> None:
        """Convenience: reload model → run hydraulics → wait → save.

        Parameters
        ----------
        model_path:
            Path to the .kdf file to reload.
        timeout:
            Maximum seconds to wait for the run to complete.
        """
        self.reload_model(model_path)
        self.run_hydraulics()
        self.wait_for_run(timeout=timeout)
        self.save_model()

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        connected = "connected" if self._app is not None else "disconnected"
        return f"KorfApp({connected}, path={self._korf_path!r})"

    def __enter__(self) -> KorfApp:
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()


# ----------------------------------------------------------------------
# Module-level convenience function
# ----------------------------------------------------------------------


def open_ui(
    file_path: str | Path,
    korf_path: str = KORF_PATH_DEFAULT,
) -> KorfApp:
    """Open a file in the **already-running** KORF instance.

    This is the recommended one-liner for interactive use.  It connects to
    the existing KORF process and loads *file_path* via ``Ctrl+O``.

    **This function never creates a new KORF instance.**

    Parameters
    ----------
    file_path:
        Path to the ``.kdf`` file to open.
    korf_path:
        Path to the KORF executable (used only to identify the running
        process, not to launch it).

    Returns
    -------
    KorfApp
        A connected :class:`KorfApp` handle that can be used for further
        automation (e.g. running hydraulics, saving).

    Raises
    ------
    AutomationError
        If no running KORF instance is found.

    Examples
    --------
    >>> from pykorf.automation import open_ui
    >>> app = open_ui("library/Pumpcases.kdf")   # doctest: +SKIP
    >>> app.run_hydraulics()                      # doctest: +SKIP
    >>> app.disconnect()                          # doctest: +SKIP
    """
    app = KorfApp.connect(korf_path=korf_path)
    app.reload_model(file_path)
    return app
