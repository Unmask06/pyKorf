"""Generate Report screen."""

from __future__ import annotations

import logging
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, LoadingIndicator, RichLog, Static, TextArea

from pykorf.use_case.config import get_last_batch_folder_path, set_last_batch_folder_path
from pykorf.use_case.tui.logging import log_error, log_info, log_success, log_warning

_logger = logging.getLogger("GenerateReport")


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
    #mode-toggle {
        height: auto;
        margin-bottom: 1;
    }
    #mode-toggle Button {
        width: 1fr;
        margin-right: 1;
    }
    #batch-input {
        height: auto;
        margin-bottom: 1;
        display: none;
    }
    #batch-input.visible {
        display: block;
    }
    #single-output-label.hidden,
    #output-path-label.hidden {
        display: none;
    }
    #single-output-label {
        margin-bottom: 1;
    }
    #folder-path-input {
        height: 4;
        margin-bottom: 1;
    }
    #file-count-label {
        color: $accent;
        margin-bottom: 1;
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
    #report-loading {
        display: none;
        height: 1;
        margin-left: 1;
    }
    #report-loading.active {
        display: block;
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

    def __init__(self, debug_mode: bool = False) -> None:
        """Initialize the generate report screen.

        Args:
            debug_mode: Whether debug logging mode is enabled.
        """
        super().__init__()
        self.debug_mode = debug_mode
        self.batch_mode = False
        self.last_output_path: str | None = None

    def compose(self) -> ComposeResult:
        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model

        output_path = "No file loaded"
        if model:
            kdf_path = Path(model._parser.path)
            output_path = str(kdf_path.with_name(f"{kdf_path.stem}_report.xlsx"))

        saved_batch_path = get_last_batch_folder_path() or ""

        with Vertical(id="report-container"), Horizontal():
            with Vertical(id="left-panel"), Vertical(id="report-form"):
                yield Label("Generate Excel Summary Report", classes="info-section")
                yield Static("─" * 30)

                with Horizontal(id="mode-toggle"):
                    yield Button("Single File", variant="primary", id="btn-mode-single")
                    yield Button("Batch Mode", variant="default", id="btn-mode-batch")

                with Vertical(id="batch-input"):
                    yield Label("Folder path:")
                    yield TextArea(text=saved_batch_path, id="folder-path-input")
                    yield Label("", id="file-count-label")

                yield Label("Output path:", id="single-output-label")
                yield Static(output_path, id="output-path-label", classes="path-display")

                yield RichLog(id="report-results", wrap=True)

                with Horizontal(id="report-buttons"):
                    yield Button("Generate Report", variant="primary", id="btn-run-generate")
                    yield Button(
                        "Open Excel", variant="default", id="btn-open-excel", disabled=True
                    )
                    yield LoadingIndicator(id="report-loading")

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
                    yield Static("• A4 Portrait layout")
                    yield Static("• Multi-index headers")
                    yield Static("• Element-specific tables")
                    yield Static("• Max 2 decimal places")
        yield Footer()

    def _get_single_file_output_path(self) -> str:
        """Get output path for single file mode."""
        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model
        if model:
            kdf_path = Path(model._parser.path)
            return str(kdf_path.with_name(f"{kdf_path.stem}_report.xlsx"))
        return "No file loaded"

    @on(Button.Pressed, "#btn-mode-single")
    def set_single_mode(self) -> None:
        """Switch to single file mode."""
        self.batch_mode = False
        self.last_output_path = None
        self.query_one("#btn-mode-single", Button).variant = "primary"
        self.query_one("#btn-mode-batch", Button).variant = "default"
        self.query_one("#batch-input", Vertical).remove_class("visible")
        self.query_one("#single-output-label", Label).remove_class("hidden")
        self.query_one("#output-path-label", Static).remove_class("hidden")
        self.query_one("#output-path-label", Static).update(self._get_single_file_output_path())
        btn = self.query_one("#btn-open-excel", Button)
        btn.disabled = True

    @on(Button.Pressed, "#btn-mode-batch")
    def set_batch_mode(self) -> None:
        """Switch to batch mode."""
        self.batch_mode = True
        self.last_output_path = None
        self.query_one("#btn-mode-batch", Button).variant = "primary"
        self.query_one("#btn-mode-single", Button).variant = "default"
        self.query_one("#batch-input", Vertical).add_class("visible")
        self.query_one("#single-output-label", Label).add_class("hidden")
        self.query_one("#output-path-label", Static).add_class("hidden")
        btn = self.query_one("#btn-open-excel", Button)
        btn.disabled = True

    @on(Button.Pressed, "#btn-open-excel")
    def open_excel(self) -> None:
        """Open the generated Excel file."""
        import os

        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)

        if self.batch_mode and self.last_output_path:
            xlsx_path = Path(self.last_output_path)
        else:
            model = app.model
            if model:
                kdf_path = Path(model._parser.path)
                xlsx_path = kdf_path.with_name(f"{kdf_path.stem}_report.xlsx")
            else:
                return

        if xlsx_path.exists():
            try:
                os.startfile(str(xlsx_path))
            except Exception as exc:
                log_error(self.query_one("#report-results", RichLog), f"Error opening file: {exc}")

    @on(Button.Pressed, "#btn-run-generate")
    def generate(self) -> None:
        self.query_one("#btn-run-generate", Button).disabled = True
        self.query_one("#report-loading").add_class("active")
        if self.batch_mode:
            self._run_batch_generate()
        else:
            self._run_generate()

    @work(thread=True)
    def _run_batch_generate(self) -> None:
        from pykorf.use_case.batch_report import BatchReportGenerator
        from pykorf.use_case.tui.app import UseCaseTUI

        results = self.query_one("#report-results", RichLog)
        app = self.app
        assert isinstance(app, UseCaseTUI)
        try:
            self.app.call_from_thread(results.clear)

            folder_input = self.query_one("#folder-path-input", TextArea)
            folder_path = folder_input.text.strip()

            if not folder_path:
                self.app.call_from_thread(lambda: log_error(results, "Please enter a folder path."))
                return

            set_last_batch_folder_path(folder_path)

            self.app.call_from_thread(
                lambda: log_info(results, f"Discovering KDF files in: {folder_path}")
            )
            generator = BatchReportGenerator(folder_path)
            count = generator.discover_files()

            if count == 0:
                self.app.call_from_thread(
                    lambda: log_error(results, f"No KDF files found in: {folder_path}")
                )
                return

            output_path = Path(folder_path) / f"{Path(folder_path).name}_batch_report.xlsx"
            preserved = generator.get_preserved_sheets(output_path)
            if preserved:
                self.app.call_from_thread(
                    lambda: log_info(results, f"Preserving existing sheets: {', '.join(preserved)}")
                )

            self.app.call_from_thread(
                lambda: log_info(results, f"Found {count} KDF file(s). Generating report...")
            )

            output_path = generator.generate_report()

            self.app.call_from_thread(
                lambda: log_success(results, "\n✅ Batch Report Generated Successfully!")
            )
            self.app.call_from_thread(lambda: log_info(results, f"Saved to: {output_path}"))

            self.last_output_path = output_path

            if generator.errors:
                self.app.call_from_thread(
                    lambda: log_warning(results, f"\n⚠ {len(generator.errors)} file(s) had errors:")
                )
                for error in generator.errors:
                    self.app.call_from_thread(lambda e=error: log_warning(results, f"  - {e}"))

            btn = self.query_one("#btn-open-excel", Button)
            btn.disabled = False
            self.app.call_from_thread(
                app.show_notification, f"✅ Batch report saved: {Path(output_path).name}"
            )

        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
        finally:

            def _finish_batch():
                self.query_one("#btn-run-generate", Button).disabled = False
                self.query_one("#report-loading").remove_class("active")

            self.app.call_from_thread(_finish_batch)

    @work(thread=True)
    def _run_generate(self) -> None:
        from pykorf.reports.exporter import ResultExporter
        from pykorf.use_case.tui.app import UseCaseTUI

        results = self.query_one("#report-results", RichLog)
        app = self.app
        assert isinstance(app, UseCaseTUI)
        model = app.model
        xlsx_path: Path | None = None
        try:
            self.app.call_from_thread(results.clear)

            if model is None:
                self.app.call_from_thread(lambda: log_error(results, "No model loaded."))
                return

            kdf_path = Path(model._parser.path)
            xlsx_path = kdf_path.with_name(f"{kdf_path.stem}_report.xlsx")

            self.app.call_from_thread(lambda: log_info(results, "Initializing exporter..."))
            self.app.call_from_thread(
                lambda: log_info(results, f"Writing to Excel: {xlsx_path.name}...")
            )

            exporter = ResultExporter(model)
            exporter.export_to_excel(str(xlsx_path))

            _logger.info("   Report complete | %s", xlsx_path.name)
            self.app.call_from_thread(
                lambda: log_success(results, "\n✅ Report Generated Successfully!")
            )
            self.app.call_from_thread(lambda: log_info(results, f"Saved to: {xlsx_path}"))

            self.last_output_path = str(xlsx_path)

            # Enable Open Excel button
            def _enable():
                btn = self.query_one("#btn-open-excel", Button)
                btn.disabled = False

            self.app.call_from_thread(_enable)

            # Show notification on main app too
            self.app.call_from_thread(app.show_notification, f"✅ Report saved: {xlsx_path.name}")

        except Exception as exc:
            _logger.error(
                "   Report failed | %s | %s",
                xlsx_path.name if xlsx_path is not None else "unknown",
                exc,
            )
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
        finally:

            def _finish_report():
                self.query_one("#btn-run-generate", Button).disabled = False
                self.query_one("#report-loading").remove_class("active")

            self.app.call_from_thread(_finish_report)
