"""Main Textual application for pyKorf use case TUI."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static


class UseCaseTUI(App):
    """pyKorf Use Case TUI - Textual application."""

    TITLE = "pyKorf Use Case Tool V0.1.0"
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
        header = self.query_one("#file-header", Label)
        header.update(f"📄 {file_path}")

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

    # Configure base logging first
    configure_logging("pykorf.log")

    # Enable debug mode if requested (sets DEBUG level)
    if debug:
        enable_debug_mode()

    app = UseCaseTUI()
    app.debug_mode = debug
    app.run()


if __name__ == "__main__":
    run_tui()
