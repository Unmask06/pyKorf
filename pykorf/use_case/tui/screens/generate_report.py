"""Generate Report screen."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Label, RichLog, Static

from pykorf.use_case.config import get_last_interaction, set_last_interaction
from pykorf.use_case.tui.logging import log_error, log_info, log_success, log_warning


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
    #element-selection {
        height: auto;
        margin-bottom: 1;
        border: solid $surface-darken-2;
        padding: 1;
    }
    #element-selection Checkbox {
        margin-bottom: 0;
        height: 3;
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

        # Load saved preferences or default to True
        prefs = get_last_interaction().get(
            "report_elements",
            {
                "Feeds": True,
                "Products": True,
                "Pipes": True,
                "Pumps": True,
                "Compressors": True,
                "Valves": True,
            },
        )

        # Determine available elements
        self.available_elements: list[str] = []
        if model:
            from pykorf.use_case.tui.screens import real_elements

            if len(real_elements(model.feeds)) > 0:
                self.available_elements.append("Feeds")
            if len(real_elements(model.products)) > 0:
                self.available_elements.append("Products")
            if len(real_elements(model.pipes)) > 0:
                self.available_elements.append("Pipes")
            if len(real_elements(model.pumps)) > 0:
                self.available_elements.append("Pumps")
            if len(real_elements(model.compressors)) > 0:
                self.available_elements.append("Compressors")
            if len(real_elements(model.valves)) > 0:
                self.available_elements.append("Valves")

        with Vertical(id="report-container"), Horizontal():
            with Vertical(id="left-panel"), Vertical(id="report-form"):
                yield Label("Generate Excel Summary Report", classes="info-section")
                yield Static("─" * 30)

                yield Label("Output path:")
                yield Static(output_path, id="output-path-label", classes="path-display")

                yield Label("Elements to include:")
                with Vertical(id="element-selection"):
                    if not self.available_elements:
                        yield Label("No exportable elements found in model.", classes="text-muted")
                    else:
                        for elem in self.available_elements:
                            yield Checkbox(
                                elem, value=prefs.get(elem, True), id=f"chk-{elem.lower()}"
                            )

                yield RichLog(id="report-results", wrap=True)

                with Horizontal(id="report-buttons"):
                    yield Button("Select All", variant="default", id="btn-select-all")
                    yield Button("Generate Report", variant="primary", id="btn-run-generate")
                    yield Button(
                        "Open Excel", variant="default", id="btn-open-excel", disabled=True
                    )

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

    @on(Button.Pressed, "#btn-select-all")
    def select_all(self) -> None:
        """Select all checkboxes."""
        if hasattr(self, "available_elements"):
            for elem in self.available_elements:
                chk_id = f"#chk-{elem.lower()}"
                self.query_one(chk_id, Checkbox).value = True

    @on(Button.Pressed, "#btn-open-excel")
    def open_excel(self) -> None:
        """Open the generated Excel file."""
        import os

        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)
        model = app.model
        if model:
            kdf_path = Path(model._parser.path)
            xlsx_path = kdf_path.with_name(f"{kdf_path.stem}_report.xlsx")
            if xlsx_path.exists():
                try:
                    os.startfile(str(xlsx_path))
                except Exception as exc:
                    log_error(
                        self.query_one("#report-results", RichLog), f"Error opening file: {exc}"
                    )

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

        # Get selected elements dynamically
        selected_elements = []
        prefs_to_save = {}

        if hasattr(self, "available_elements"):
            for elem in self.available_elements:
                chk_id = f"#chk-{elem.lower()}"
                is_checked = self.query_one(chk_id, Checkbox).value
                prefs_to_save[elem] = is_checked
                if is_checked:
                    selected_elements.append(elem)

        # Save preferences
        current_data = get_last_interaction()
        current_data["report_elements"] = prefs_to_save
        set_last_interaction("generate_report", current_data)

        if not selected_elements:
            self.app.call_from_thread(
                lambda: log_warning(results, "No elements selected for export.")
            )
            return

        try:
            kdf_path = Path(model._parser.path)
            xlsx_path = kdf_path.with_name(f"{kdf_path.stem}_report.xlsx")

            self.app.call_from_thread(lambda: log_info(results, "Initializing exporter..."))
            exporter = ResultExporter(model)

            self.app.call_from_thread(
                lambda: log_info(
                    results, f"Generating summary data for: {', '.join(selected_elements)}"
                )
            )
            self.app.call_from_thread(
                lambda: log_info(results, f"Writing to Excel: {xlsx_path.name}...")
            )

            exporter.export_to_excel(str(xlsx_path), elements=selected_elements)

            self.app.call_from_thread(
                lambda: log_success(results, "\n✅ Report Generated Successfully!")
            )
            self.app.call_from_thread(lambda: log_info(results, f"Saved to: {xlsx_path}"))

            # Enable Open Excel button
            def _enable():
                btn = self.query_one("#btn-open-excel", Button)
                btn.disabled = False

            self.app.call_from_thread(_enable)

            # Show notification on main app too
            self.app.call_from_thread(app.show_notification, f"✅ Report saved: {xlsx_path.name}")

        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Error: {e}"))
