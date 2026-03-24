"""File picker screen for KDF file selection."""

from __future__ import annotations

import datetime
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, TextArea

from pykorf.use_case.config import (
    get_last_kdf_path,
    get_recent_files,
    record_opened_file,
)
from pykorf.use_case.tui.screens import normalize_path_input, real_elements

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
        max-height: 44;
        border: round $accent;
        padding: 1 2;
    }
    #file-picker-box > Label {
        margin-bottom: 1;
    }
    #file-name-label {
        color: $success;
        text-style: bold;
        height: auto;
        margin-bottom: 0;
    }
    #file-path-input {
        height: 6;
        margin-bottom: 1;
    }
    #file-info {
        color: $success;
        height: auto;
        margin-bottom: 0;
    }
    #file-error {
        color: $error;
        height: auto;
        margin-bottom: 1;
    }
    #recent-files-section {
        height: auto;
        margin-bottom: 1;
        display: none;
    }
    #recent-files-section.visible {
        display: block;
    }
    #recent-files-label {
        color: $text-muted;
        margin-bottom: 0;
    }
    #recent-files-list {
        height: auto;
        max-height: 8;
    }
    .recent-file-btn {
        width: 1fr;
        height: 1;
        margin: 0;
        background: $surface;
        border: none;
        text-align: left;
        color: $text;
    }
    .recent-file-btn:hover {
        background: $accent 30%;
    }
    #file-picker-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    #file-picker-buttons Button {
        margin: 0 1;
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
            yield Label("Drag & drop a KDF file onto this window  —  or enter the path manually:")
            yield Label("", id="file-name-label")
            yield TextArea(
                text="",
                id="file-path-input",
            )
            yield Label("", id="file-info")
            yield Label("", id="file-error")
            with Vertical(id="recent-files-section"):
                yield Label("Recent Files:", id="recent-files-label")
                with VerticalScroll(id="recent-files-list"):
                    pass
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

        self._populate_recent_files()

    def _populate_recent_files(self) -> None:
        recent = get_recent_files()
        if not recent:
            return

        section = self.query_one("#recent-files-section")
        section.add_class("visible")

        recent_list = self.query_one("#recent-files-list")
        for i, path_str in enumerate(recent):
            p = Path(path_str)
            label = p.name if len(path_str) > 60 else path_str
            btn = Button(label, classes="recent-file-btn", id=f"recent-{i}")
            btn.tooltip = path_str
            recent_list.mount(btn)

    @on(Button.Pressed, ".recent-file-btn")
    def select_recent_file(self, event: Button.Pressed) -> None:
        tooltip = event.button.tooltip
        if tooltip:
            input_widget = self.query_one("#file-path-input", TextArea)
            input_widget.text = str(tooltip)  # fires TextArea.Changed → _validate_path

    @on(TextArea.Changed, "#file-path-input")
    def on_path_changed(self, event: TextArea.Changed) -> None:
        self._validate_path(normalize_path_input(event.text_area.text))

    def _validate_path(self, raw_path: str) -> None:
        info_label = self.query_one("#file-info", Label)
        error_label = self.query_one("#file-error", Label)
        name_label = self.query_one("#file-name-label", Label)

        info_label.update("")
        error_label.update("")
        name_label.update("")

        if not raw_path:
            return

        try:
            path = Path(raw_path).resolve()
        except (OSError, ValueError):
            return

        if not path.exists():
            error_label.update(f"File not found: {path}")
            return

        if not path.is_file():
            error_label.update(f"Not a file: {path}")
            return

        if path.suffix.lower() != ".kdf":
            error_label.update(f"Not a .kdf file: {path.suffix}")
            return

        try:
            stat = path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            if size_mb >= 1:
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = f"{stat.st_size / 1024:.1f} KB"
            name_label.update(path.name)
            info_label.update(f"✓  {size_str}  |  Modified: {modified}")
        except OSError:
            name_label.update(path.name)
            info_label.update("✓ Valid .kdf file")

    @on(Button.Pressed, "#btn-clear")
    def clear_path(self) -> None:
        input_widget = self.query_one("#file-path-input", TextArea)
        input_widget.text = ""
        self.query_one("#file-info", Label).update("")
        self.query_one("#file-error", Label).update("")
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
        raw_path = normalize_path_input(path_input.text)

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

            log_file_path = path.parent / f"{path.stem}.log"
            set_log_file(log_file_path)

            model = Model(str(path))
            pipe_count = len(real_elements(model.pipes))
            error_label.update(f"Loaded {pipe_count} pipes.")

            record_opened_file(path)

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
