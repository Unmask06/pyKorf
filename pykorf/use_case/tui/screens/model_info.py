"""Model info screen."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, RichLog, Static


class ModelInfoScreen(Screen):
    """Screen displaying model element counts and pipe names."""

    BINDINGS = [("escape", "go_back", "Back")]

    CSS = """
    ModelInfoScreen {
        align: center middle;
    }
    #info-box {
        width: 80;
        height: auto;
        max-height: 40;
        border: round $accent;
        padding: 1 2;
    }
    #info-box Label {
        margin-bottom: 1;
    }
    #info-table {
        height: auto;
        max-height: 8;
        margin-bottom: 1;
    }
    #pipe-list {
        height: auto;
        max-height: 20;
        border: round $surface;
        margin-bottom: 1;
        overflow-x: hidden;
    }
    #pipe-list RichLog {
        overflow-x: hidden;
    }
    #info-buttons {
        height: 3;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model
        assert model is not None

        from pykorf.use_case.tui.screens import real_elements

        pipes = real_elements(model.pipes)
        feeds = real_elements(model.feeds)
        products = real_elements(model.products)
        pumps = real_elements(model.pumps)
        valves = real_elements(model.valves)

        with Vertical(id="info-box"):
            yield Label("Model Information")
            yield Label(f"File: {model._parser.path}")
            yield Static("---")

            table = DataTable(id="info-table")
            table.add_columns("Element Type", "Count")
            table.add_rows(
                [
                    ("Pipes", str(len(pipes))),
                    ("Feeds", str(len(feeds))),
                    ("Products", str(len(products))),
                    ("Pumps", str(len(pumps))),
                    ("Valves", str(len(valves))),
                ]
            )
            yield table

            yield Label("Pipe Names:")
            log = RichLog(id="pipe-list", wrap=True)
            yield log

            with Horizontal(id="info-buttons"):
                yield Button("Back", variant="default", id="btn-back")

        yield Footer()

    def on_mount(self) -> None:
        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)
        model = app.model
        assert model is not None

        from pykorf.use_case.tui.screens import real_elements

        log = self.query_one("#pipe-list", RichLog)
        pipes = real_elements(model.pipes)
        for idx, pipe in sorted(pipes.items()):
            if pipe.name:
                log.write(f"  {pipe.name}")
        if not any(p.name for p in pipes.values()):
            log.write("  (no named pipes)")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()
