"""Main Textual application for pyKorf use case TUI."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static

from pykorf import __version__


class UseCaseTUI(App):
    """pyKorf Use Case TUI - Textual application."""

    TITLE = f"pyKorf Use Case Tool V{__version__}"
    SUB_TITLE = "Bulk operations on KDF files"
    CSS_PATH = []

    CSS = """
    Screen {
        background: $surface;
    }
    #app-container {
        width: 100%;
        height: 100%;
    }
    #file-header {
        dock: top;
        width: 100%;
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        content-align: right middle;
        text-style: dim;
        padding: 0 2;
    }
    #notification-banner {
        dock: top;
        width: 100%;
        height: auto;
        background: $warning-darken-2;
        color: $text;
        content-align: center middle;
        text-style: bold;
        padding: 1;
        display: none;
    }
    #notification-banner.visible {
        display: block;
    }
    #left-panel {
        width: 70%;
        height: 100%;
        border-right: solid $surface-darken-2;
    }
    #right-panel {
        width: 30%;
        height: 100%;
        padding: 0 1;
    }
    .side-panel-section {
        margin-bottom: 1;
    }
    .side-panel-section Label {
        text-style: bold;
        color: $accent;
    }
    .side-panel-section Static {
        color: $text-muted;
        text-style: dim;
    }
    .compact-button {
        height: 3;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "reload_file", "Reload"),
        ("escape", "pop_screen", "Back"),
    ]

    model = None
    debug_mode: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="app-container"):
            yield Label("📄 No file loaded", id="file-header")
            yield Static("", id="notification-banner")

    def on_mount(self) -> None:
        from pykorf.use_case.tui.screens.file_picker import FilePickerScreen

        self.push_screen(FilePickerScreen(debug_mode=self.debug_mode))

    def update_file_header(self, file_path: str) -> None:
        """Update the file header with the current KDF path."""
        from pathlib import Path

        header = self.query_one("#file-header", Label)
        header.update(f"📄 {Path(file_path).name}")

    def action_reload_file(self) -> None:
        """Reload the current KDF file from disk."""
        if self.model is None:
            return

        try:
            self.model.reload()
            self.show_notification("File reloaded successfully")
            # If we are on MainMenu, we might want to refresh it
            from pykorf.use_case.tui.screens.main_menu import MainMenuScreen

            if isinstance(self.screen, MainMenuScreen):
                self.pop_screen()
                self.push_screen(MainMenuScreen())
        except Exception as exc:
            self.show_notification(f"Error reloading file: {exc}")

    def action_pop_screen(self) -> None:
        """Override pop_screen to prevent exiting the first screen (FilePicker)."""
        from pykorf.use_case.tui.screens.file_picker import FilePickerScreen

        if isinstance(self.screen, FilePickerScreen):
            return
        super().pop_screen()

    def show_notification(self, message: str) -> None:
        """Show a notification banner with the given message."""
        banner = self.query_one("#notification-banner", Static)
        banner.update(message)
        banner.add_class("visible")

    def hide_notification(self) -> None:
        """Hide the notification banner."""
        banner = self.query_one("#notification-banner", Static)
        banner.remove_class("visible")


def run_tui(debug: bool = False) -> None:
    """Launch the Textual TUI application.

    Args:
        debug: Enable debug mode logging.
    """
    from pykorf.log import configure_logging, enable_debug_mode

    # Configure logging with a temporary log file initially
    # The actual log file will be set when a KDF file is loaded
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as temp_log:
        temp_log_path = temp_log.name

    configure_logging(temp_log_path)

    # Enable debug mode if requested (sets DEBUG level)
    if debug:
        enable_debug_mode()

    app = UseCaseTUI()
    app.debug_mode = debug
    app.run()


if __name__ == "__main__":
    run_tui()
