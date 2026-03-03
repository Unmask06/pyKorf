"""Main menu screen with use case options."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static


class MainMenuScreen(Screen):
    """Central menu showing use-case operations."""

    BINDINGS = [
        ("1", "bulk_copy", "Bulk Copy Fluids"),
        ("2", "apply_pms", "Apply PMS"),
        ("3", "apply_hmb", "Apply HMB"),
        ("4", "model_info", "Model Info"),
        ("l", "load_file", "Load File"),
        ("q", "quit_app", "Quit"),
    ]

    CSS = """
    MainMenuScreen {
        align: center middle;
    }
    #menu-box {
        width: 70;
        height: auto;
        max-height: 30;
        border: round $accent;
        padding: 1 2;
    }
    #menu-box Label {
        margin-bottom: 1;
    }
    #menu-buttons Button {
        width: 100%;
        margin-bottom: 1;
    }
    #menu-footer {
        height: 3;
        align: center middle;
    }
    #menu-footer Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model

        file_name = "No file loaded"
        pipe_count = 0
        if model is not None:
            file_name = str(model._parser.path)
            from pykorf.use_case.tui.screens import real_elements

            pipe_count = len(real_elements(model.pipes))

        with Vertical(id="menu-box"):
            yield Label(f"[bold]File:[/bold] {file_name}")
            yield Label(f"[bold]Pipes:[/bold] {pipe_count}")
            yield Static("---")
            with Vertical(id="menu-buttons"):
                yield Button(
                    "[1] Bulk Copy Fluids",
                    variant="primary",
                    id="btn-bulk-copy",
                )
                yield Button(
                    "[2] Apply PMS Specifications",
                    variant="primary",
                    id="btn-apply-pms",
                )
                yield Button(
                    "[3] Apply HMB Fluid Properties",
                    variant="primary",
                    id="btn-apply-hmb",
                )
                yield Button(
                    "[4] View Model Info",
                    variant="primary",
                    id="btn-model-info",
                )
            yield Static("---")
            with Horizontal(id="menu-footer"):
                yield Button(
                    "[L] Load Different File",
                    variant="warning",
                    id="btn-load-file",
                )
                yield Button("[Q] Quit", variant="error", id="btn-quit")
        yield Footer()

    @on(Button.Pressed, "#btn-bulk-copy")
    def action_bulk_copy(self) -> None:
        from pykorf.use_case.tui.screens.bulk_copy import BulkCopyFluidsScreen

        self.app.push_screen(BulkCopyFluidsScreen())

    @on(Button.Pressed, "#btn-apply-pms")
    def action_apply_pms(self) -> None:
        from pykorf.use_case.tui.screens.apply_pms import ApplyPmsScreen

        self.app.push_screen(ApplyPmsScreen())

    @on(Button.Pressed, "#btn-apply-hmb")
    def action_apply_hmb(self) -> None:
        from pykorf.use_case.tui.screens.apply_hmb import ApplyHmbScreen

        self.app.push_screen(ApplyHmbScreen())

    @on(Button.Pressed, "#btn-model-info")
    def action_model_info(self) -> None:
        from pykorf.use_case.tui.screens.model_info import ModelInfoScreen

        self.app.push_screen(ModelInfoScreen())

    @on(Button.Pressed, "#btn-load-file")
    def action_load_file(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-quit")
    def action_quit_app(self) -> None:
        self.app.exit()
