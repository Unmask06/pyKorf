"""Model info screen with validation display."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, RichLog, Static


class ModelInfoScreen(Screen):
    """Screen displaying model element counts, pipe names, and validation errors."""

    BINDINGS = [("escape", "go_back", "Back")]

    CSS = """
    ModelInfoScreen {
        align: center middle;
    }
    #info-box {
        width: 90;
        height: auto;
        max-height: 45;
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
    #pipe-list, #validation-list {
        height: auto;
        max-height: 15;
        border: round $surface;
        margin-bottom: 1;
        overflow-x: hidden;
    }
    #pipe-list RichLog, #validation-list RichLog {
        overflow-x: hidden;
    }
    #validation-list {
        border: round $error;
    }
    #validation-header {
        color: $text;
        text-style: bold;
    }
    #validation-header.error {
        color: $error;
    }
    #validation-header.success {
        color: $success;
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

        # Get validation issues
        validation_issues = model.validate()

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
            log = RichLog(id="pipe-list", wrap=True, highlight=True)
            yield log

            # Validation section
            yield Static("---")
            validation_header = (
                f"Validation: PASSED ({len(validation_issues)} issues)"
                if not validation_issues
                else f"Validation: FAILED ({len(validation_issues)} issues)"
            )
            yield Label(validation_header, id="validation-header")

            if validation_issues:
                val_log = RichLog(id="validation-list", wrap=True, highlight=True)
                yield val_log

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

        # Populate pipe list
        log = self.query_one("#pipe-list", RichLog)
        pipes = real_elements(model.pipes)
        for idx, pipe in sorted(pipes.items()):
            if pipe.name:
                log.write(f"  {pipe.name}")
        if not any(p.name for p in pipes.values()):
            log.write("  (no named pipes)")

        # Populate validation list
        validation_issues: list[str] = model.validate()
        validation_header = self.query_one("#validation-header", Label)

        if validation_issues:
            # Show issues in red
            validation_header.add_class("error")
            validation_header.update(f"Validation: FAILED ({len(validation_issues)} issues)")

            val_log = self.query_one("#validation-list", RichLog)
            for issue in validation_issues:
                # Categorize issues by type for better display
                if "NUM" in issue:
                    prefix = "[NUM]"
                elif "NAME" in issue or "missing NAME" in issue:
                    prefix = "[NAME]"
                elif "CON" in issue or "references" in issue:
                    prefix = "[CONN]"
                elif "NOTES" in issue:
                    prefix = "[NOTES]"
                elif "empty" in issue or "whitespace" in issue:
                    prefix = "[VALUE]"
                elif "Layout" in issue or "overlap" in issue or "clash" in issue:
                    prefix = "[LAYOUT]"
                elif "connectivity" in issue.lower():
                    prefix = "[CONN]"
                elif "missing" in issue.lower() or "required" in issue.lower():
                    prefix = "[REQUIRED]"
                else:
                    prefix = "[INFO]"

                val_log.write(f"{prefix} {issue}")
        else:
            # No issues - show green
            validation_header.add_class("success")
            validation_header.update("Validation: PASSED (no issues)")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()
