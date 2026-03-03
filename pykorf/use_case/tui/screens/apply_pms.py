"""Apply PMS screen."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Static


class ApplyPmsScreen(Screen):
    """Screen for applying PMS specifications to pipes."""

    BINDINGS = [("escape", "go_back", "Back")]

    CSS = """
    ApplyPmsScreen {
        align: center middle;
    }
    #pms-box {
        width: 80;
        height: auto;
        max-height: 40;
        border: round $accent;
        padding: 1 2;
    }
    #pms-box Label {
        margin-bottom: 1;
    }
    #pms-box Input {
        margin-bottom: 1;
    }
    #pms-buttons {
        height: 3;
        align: center middle;
    }
    #pms-buttons Button {
        margin: 0 1;
    }
    #pms-results {
        height: 12;
        border: round $surface;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="pms-box"):
            yield Label("[bold]Apply PMS Specifications[/bold]")
            yield Static("---")
            yield Label("PMS JSON file path:")
            yield Input(
                placeholder="C:\\path\\to\\pms.json",
                id="pms-path-input",
            )
            yield RichLog(id="pms-results", wrap=True)
            with Horizontal(id="pms-buttons"):
                yield Button("Apply", variant="primary", id="btn-apply")
                yield Button("Back", variant="default", id="btn-back")
        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-apply")
    def apply(self) -> None:
        self._run_apply()

    @work(thread=True)
    def _run_apply(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.save_confirm import SaveConfirmScreen

        results = self.query_one("#pms-results", RichLog)
        raw_path = self.query_one("#pms-path-input", Input).value.strip().strip('"').strip("'")

        self.app.call_from_thread(results.clear)

        if not raw_path:
            self.app.call_from_thread(results.write, "[red]Please enter a PMS file path.[/red]")
            return

        path = Path(raw_path)
        if not path.exists():
            self.app.call_from_thread(results.write, f"[red]File not found: {path}[/red]")
            return

        self.app.call_from_thread(results.write, "Applying PMS specifications...")

        try:
            from pykorf.use_case import apply_pms

            app = self.app
            assert isinstance(app, UseCaseTUI)
            model = app.model
            assert model is not None

            updated = apply_pms(str(path), model, save=False)
            self.app.call_from_thread(
                results.write,
                f"[green]Applied PMS specs to {len(updated)} pipes.[/green]",
            )
            for name in updated:
                self.app.call_from_thread(results.write, f"  - {name}")
            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))
        except Exception as exc:
            self.app.call_from_thread(results.write, f"[red]Error: {exc}[/red]")
