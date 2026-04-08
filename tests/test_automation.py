"""
Tests for pykorf.automation - open_ui and KorfApp.

Since pywinauto is a Windows-only dependency, all tests mock the
underlying Application object so they can run on any platform.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pykorf.app.automation import KorfApp
from pykorf.core.exceptions import AutomationError

# ------------------------------------------------------------------
# KorfApp tests (with pywinauto mocked)
# ------------------------------------------------------------------


class TestKorfApp:
    """Test KorfApp behaviour when pywinauto is available (mocked)."""

    def _make_app(self):
        """Create a KorfApp with a mocked internal _app attribute."""
        mock_app_instance = MagicMock()
        mock_window = MagicMock()
        mock_window.window_text.return_value = "KORF - [Pumpcases.kdf]"
        mock_app_instance.top_window.return_value = mock_window

        app = KorfApp.__new__(KorfApp)
        app._korf_path = r"C:\Program Files (x86)\Korf 36\Korf_36.exe"
        app._app = mock_app_instance
        return app, mock_app_instance, mock_window

    def test_repr_connected(self):
        app, _, _ = self._make_app()
        assert "connected" in repr(app)

    def test_repr_disconnected(self):
        app, _, _ = self._make_app()
        app.disconnect()
        assert "disconnected" in repr(app)

    def test_window_title(self):
        app, _, mock_window = self._make_app()
        assert app.window_title == "KORF - [Pumpcases.kdf]"

    def test_require_connected_raises(self):
        app, _, _ = self._make_app()
        app.disconnect()
        with pytest.raises(AutomationError, match="Not connected"):
            app._require_connected()

    def test_context_manager(self):
        app, _, _ = self._make_app()
        with app as a:
            assert a._app is not None
        assert a._app is None


# ------------------------------------------------------------------
# open_ui tests
# ------------------------------------------------------------------


class TestOpenUi:
    """Test the module-level open_ui convenience function."""

    def test_open_ui_connects_and_reloads(self):
        """open_ui must connect to KORF and reload the model, never start a new process."""
        mock_app = MagicMock()

        with patch("pykorf.app.automation.KorfApp") as MockKorfApp:
            MockKorfApp.connect.return_value = mock_app
            from pykorf.app.automation import open_ui

            result = open_ui("library/Pumpcases.kdf")

            MockKorfApp.connect.assert_called_once()
            mock_app.reload_model.assert_called_once_with("library/Pumpcases.kdf")
            assert result is mock_app

    def test_open_ui_passes_korf_path(self):
        """open_ui forwards the korf_path argument to KorfApp.connect."""
        mock_app = MagicMock()
        custom_path = r"D:\CustomKorf\korf.exe"

        with patch("pykorf.app.automation.KorfApp") as MockKorfApp:
            MockKorfApp.connect.return_value = mock_app
            from pykorf.app.automation import open_ui

            open_ui("model.kdf", korf_path=custom_path)

            MockKorfApp.connect.assert_called_once_with(korf_path=custom_path)

    def test_open_ui_propagates_error(self):
        """open_ui raises AutomationError if no KORF instance is running."""
        with patch("pykorf.app.automation.KorfApp") as MockKorfApp:
            MockKorfApp.connect.side_effect = AutomationError("KORF not running")
            from pykorf.app.automation import open_ui

            with pytest.raises(AutomationError, match="KORF not running"):
                open_ui("model.kdf")

    def test_open_ui_accepts_pathlib_path(self):
        """open_ui accepts both str and pathlib.Path for the file path."""
        mock_app = MagicMock()

        with patch("pykorf.app.automation.KorfApp") as MockKorfApp:
            MockKorfApp.connect.return_value = mock_app
            from pykorf.app.automation import open_ui

            open_ui(Path("library/Pumpcases.kdf"))

            mock_app.reload_model.assert_called_once_with(Path("library/Pumpcases.kdf"))


class TestOpenUiNeverStartsKorf:
    """Verify that open_ui never launches a new KORF process.

    This is the **most critical** safety requirement of the package.
    """

    def test_no_start_call(self):
        """The Application.start() method must never be called."""
        mock_app = MagicMock()

        with patch("pykorf.app.automation.KorfApp") as MockKorfApp:
            MockKorfApp.connect.return_value = mock_app
            from pykorf.app.automation import open_ui

            open_ui("model.kdf")

            # connect() is allowed; start() is not
            MockKorfApp.connect.assert_called_once()
            MockKorfApp.start.assert_not_called()
