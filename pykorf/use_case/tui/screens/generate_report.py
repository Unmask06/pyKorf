"""Generate Report screen."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, RichLog, Static

from pykorf.use_case.tui.logging import log_error, log_info, log_success


class GenerateReportScreen(Screen):
    """Screen for generating Excel summary reports."""

    CSS_PATH = []

    CSS = """
    GenerateReportScreen {
        align: center middle;
    }
    #report-container {
        width: 100%;
        height: 100%;
    }
    #report-form {
        padding: 0 1;
    }
    #report-form Label {
        margin-bottom: 1;
        height: auto;
    }
    #report-buttons {
        height: auto;
        margin-top: 1;
    }
    #report-buttons Button {
        margin-right: 1;
        height: 3;
        padding: 0 1;
    }
    #report-results {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #report-results RichLog {
        overflow-x: hidden;
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
    .path-display {
        color: $text-muted;
        background: $surface-darken-1;
        padding: 1;
        border: solid $surface;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI
        assert isinstance(app, UseCaseTUI)
        model = app.model
        
        output_path = "No file loaded"
        if model:
            kdf_path = Path(model._parser.path)
            output_path = str(kdf_path.with_name(f"{kdf_path.stem}_report.xlsx"))

        with Vertical(id="report-container"), Horizontal():
            with Vertical(id="left-panel"), Vertical(id="report-form"):
                yield Label("Generate Excel Summary Report", classes="info-section")
                yield Static("─" * 30)
                yield Label("Output path:")
                yield Static(output_path, id="output-path-label", classes="path-display")
                
                yield RichLog(id="report-results", wrap=True)
                
                with Horizontal(id="report-buttons"):
                    yield Button("Generate Report", variant="primary", id="btn-run-generate")
                    yield Button("Back", variant="default", id="btn-back")

            with Vertical(id="right-panel"):
                with Vertical(classes="info-section"):
                    yield Label("About Reports")
                    yield Static("─" * 15)
                    yield Static("Generates a single-sheet")
                    yield Static("Excel summary of all")
                    yield Static("core elements.")
                    yield Static("")
                    yield Static("Includes automated unit")
                    yield Static("conversions and clean")
                    yield Static("formatting.")

                with Vertical(classes="info-section"):
                    yield Label("Format")
                    yield Static("─" * 15)
                    yield Static("• A4 Landscape layout")
                    yield Static("• Multi-index headers")
                    yield Static("• Element-specific tables")
                    yield Static("• Max 2 decimal places")
        yield Footer()

    @on(Button.Pressed, "#btn-back")
    def back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-run-generate")
    def generate(self) -> None:
        self._run_generate()

    @work(thread=True)
    def _run_generate(self) -> None:
        from pykorf.reports.exporter import ResultExporter
        from pykorf.use_case.tui.app import UseCaseTUI

        results = self.query_one("#report-results", RichLog)
        app = self.app
        assert isinstance(app, UseCaseTUI)
        model = app.model

        self.app.call_from_thread(results.clear)

        if model is None:
            self.app.call_from_thread(lambda: log_error(results, "No model loaded."))
            return

        try:
            kdf_path = Path(model._parser.path)
            xlsx_path = kdf_path.with_name(f"{kdf_path.stem}_report.xlsx")

            self.app.call_from_thread(lambda: log_info(results, f"Initializing exporter..."))
            exporter = ResultExporter(model)
            
            self.app.call_from_thread(lambda: log_info(results, f"Generating summary data..."))
            self.app.call_from_thread(lambda: log_info(results, f"Writing to Excel: {xlsx_path.name}..."))
            
            exporter.export_to_excel(str(xlsx_path))

            self.app.call_from_thread(lambda: log_success(results, "\n✅ Report Generated Successfully!"))
            self.app.call_from_thread(lambda: log_info(results, f"Saved to: {xlsx_path}"))
            
            # Show notification on main app too
            self.app.call_from_thread(app.show_notification, f"✅ Report saved: {xlsx_path.name}")
            
        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
