"""Shared header widget showing current KDF file."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, Static


class KdfFileHeader(Static):
    """Persistent header showing the current KDF file path."""

    CSS = """
    KdfFileHeader {
        width: 100%;
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        content-align: center middle;
        text-style: dim;
    }
    """

    def __init__(self, file_path: str | None = None) -> None:
        super().__init__()
        self.file_path = file_path or "No file loaded"

    def compose(self) -> ComposeResult:
        yield Label(f"📄 {self.file_path}")

    def update_path(self, file_path: str) -> None:
        """Update the displayed file path."""
        self.file_path = file_path
        label = self.query_one(Label)
        label.update(f"📄 {file_path}")
