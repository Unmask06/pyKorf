"""File picker screen for KDF file selection."""

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, TextArea

from pykorf.use_case.config import get_last_kdf_path, set_last_kdf_path
from pykorf.use_case.tui.screens import real_elements

MAX_FILE_SIZE_MB = 100


class FilePickerScreen(Screen):
    """Screen for selecting a KDF file to load."""

    CSS_PATH = []

    CSS = """
    FilePickerScreen {
        align: center middle;
    }
    #file-picker-box {
        width: 80;
        height: auto;
        max-height: 25;
        border: round $accent;
        padding: 1 2;
    }
    #file-picker-box Label {
        margin-bottom: 1;
    }
    #file-path-input {
        height: 6;
        margin-bottom: 1;
    }
    #file-picker-buttons {
        height: 3;
        align: center middle;
    }
    #file-picker-buttons Button {
        margin: 0 1;
    }
    #file-error {
        color: $error;
        height: auto;
        margin-bottom: 1;
    }
    """

    def __init__(self, debug_mode: bool = False) -> None:
        """Initialize the file picker screen.

        Args:
            debug_mode: Whether debug logging mode is enabled.
        """
        super().__init__()
        self.debug_mode = debug_mode

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="file-picker-box"):
            yield Label("Enter the path to a KDF file:")
            yield TextArea(
                text="",
                id="file-path-input",
            )
            yield Label("", id="file-error")
            with Horizontal(id="file-picker-buttons"):
                yield Button("Load", variant="primary", id="btn-load")
                yield Button("Clear", variant="warning", id="btn-clear")
                yield Button("Quit", variant="error", id="btn-quit")
        yield Footer()

    def on_mount(self) -> None:
        last_path = get_last_kdf_path()
        if last_path:
            input_widget = self.query_one("#file-path-input", TextArea)
            input_widget.text = str(last_path)

    @on(Button.Pressed, "#btn-clear")
    def clear_path(self) -> None:
        input_widget = self.query_one("#file-path-input", TextArea)
        input_widget.text = ""
        input_widget.focus()

    @on(Button.Pressed, "#btn-quit")
    def quit_app(self) -> None:
        self.app.exit()

    @on(Button.Pressed, "#btn-load")
    def load_file(self) -> None:
        self._try_load()

    def _try_load(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.main_menu import MainMenuScreen

        path_input = self.query_one("#file-path-input", TextArea)
        error_label = self.query_one("#file-error", Label)
        # Remove any newlines that might be pasted and strip quotes
        raw_path = path_input.text.replace("\n", "").strip().strip('"').strip("'")

        if not raw_path:
            error_label.update("Please enter a file path.")
            return

        path = Path(raw_path)

        try:
            path = path.resolve()
        except (OSError, ValueError) as e:
            error_label.update(f"Invalid path: {e}")
            return

        if not path.exists():
            error_label.update(f"File not found: {path}")
            return

        if not path.is_file():
            error_label.update(f"Not a file: {path}")
            return

        try:
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                error_label.update(
                    f"File too large: {file_size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"
                )
                return
        except OSError as e:
            error_label.update(f"Cannot read file stats: {e}")
            return

        if path.suffix.lower() != ".kdf":
            error_label.update(f"Invalid file type: {path.suffix}. Please select a .kdf file.")
            return

        try:
            from pykorf import Model
            from pykorf.log import enable_debug_mode, set_log_file

            # Set log file to KDF file's directory with same name prefix
            log_file_path = path.parent / f"{path.stem}.log"
            set_log_file(log_file_path)

            model = Model(str(path))
            pipe_count = len(real_elements(model.pipes))
            error_label.update(f"Loaded {pipe_count} pipes.")

            set_last_kdf_path(path)

            # Set up debug log file if in debug mode
            if self.debug_mode:
                debug_log_path = path.parent / f"{path.stem}-debug.log"
                enable_debug_mode(debug_log_path)

            app = self.app
            assert isinstance(app, UseCaseTUI)
            app.model = model
            app.update_file_header(str(path))
            self.app.push_screen(MainMenuScreen())
        except Exception as exc:
            error_label.update(f"Error loading file: {exc}")
