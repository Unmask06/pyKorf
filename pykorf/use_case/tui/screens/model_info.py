"""Model info screen with validation display."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Label, RichLog, Static


class ModelInfoScreen(Screen):
    """Screen displaying model element counts, pipe names, and validation errors."""

    CSS_PATH = []

    CSS = """
    ModelInfoScreen {
        align: center middle;
    }
    #info-container {
        width: 100%;
        height: 100%;
    }
    #info-table {
        height: auto;
        max-height: 8;
        margin-bottom: 1;
    }
    #pipe-list, #validation-list {
        height: 1fr;
        border: round $surface;
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
    #right-panel-content {
        padding: 0 1;
    }
    .info-section {
        margin-bottom: 1;
    }
    .info-section Label {
        text-style: bold;
        color: $accent;
    }
    .stat-row {
        height: 1;
        margin-bottom: 0;
    }
    """

    def compose(self) -> ComposeResult:
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

        validation_issues = model.validate()

        with Vertical(id="info-container"):
            with Horizontal():
                with Vertical(id="left-panel"):
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

                    yield Label("Pipe Names:", classes="info-section")
                    log = RichLog(id="pipe-list", wrap=True, highlight=True)
                    yield log

                    yield Static("---")
                    validation_header = (
                        f"PASSED ({len(validation_issues)} issues)"
                        if not validation_issues
                        else f"FAILED ({len(validation_issues)} issues)"
                    )
                    yield Label(f"Validation: {validation_header}", id="validation-header")

                    if validation_issues:
                        val_log = RichLog(id="validation-list", wrap=True, highlight=True)
                        yield val_log

                    with Horizontal(id="info-buttons"):
                        yield Button("Back", variant="default", id="btn-back")

                with Vertical(id="right-panel"):
                    with Vertical(classes="info-section"):
                        yield Label("Quick Stats")
                        yield Static("─" * 15)
                        yield Static(
                            f"Total Elements: {len(pipes) + len(feeds) + len(products) + len(pumps) + len(valves)}"
                        )
                        yield Static(f"Pipes: {len(pipes)}")
                        yield Static(f"Feeds: {len(feeds)}")
                        yield Static(f"Products: {len(products)}")

                    with Vertical(classes="info-section"):
                        yield Label("Validation")
                        yield Static("─" * 15)
                        if validation_issues:
                            yield Static(f"⚠ {len(validation_issues)} issues found")
                            yield Static("")
                            yield Static("Review issues in")
                            yield Static("left panel.")
                        else:
                            yield Static("✓ No issues")
                            yield Static("Model is valid.")

                    with Vertical(classes="info-section"):
                        yield Label("Tips")
                        yield Static("─" * 15)
                        yield Static("Fix validation issues")
                        yield Static("before saving changes.")
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

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()
