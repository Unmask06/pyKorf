"""Import/Export Excel screen for model I/O."""

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, RichLog, Static, TextArea

from pykorf.use_case.config import (
    get_last_excel_export_path,
    get_last_excel_import_path,
    set_last_excel_export_path,
    set_last_excel_import_path,
)
from pykorf.use_case.tui.logging import log_error, log_info, log_success, log_warning


class ImportExportScreen(Screen):
    """Screen for importing/exporting models to/from Excel."""

    CSS_PATH = []

    CSS = """
    ImportExportScreen {
        align: center middle;
    }
    #import-export-container {
        width: 100%;
        height: 100%;
    }
    #mode-toggle {
        height: auto;
        margin-bottom: 1;
    }
    #mode-toggle Button {
        width: 1fr;
        margin-right: 1;
    }
    #export-panel, #import-panel {
        height: auto;
        margin-bottom: 1;
    }
    #import-path-input {
        height: 4;
        margin-bottom: 1;
    }
    #file-picker-buttons {
        height: auto;
        margin-bottom: 1;
    }
    #file-picker-buttons Button {
        margin-right: 1;
    }
    .hidden {
        display: none;
    }
    .path-display {
        color: $text-muted;
        background: $surface-darken-1;
        padding: 1;
        border: solid $surface;
        margin-bottom: 1;
    }
    #action-buttons {
        height: auto;
        margin-top: 1;
    }
    #action-buttons Button {
        margin-right: 1;
    }
    #results-log {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
    }
    #confirm-dialog {
        dock: top;
        width: 100%;
        height: auto;
        background: $warning-darken-2;
        padding: 1;
        display: none;
    }
    #confirm-dialog.visible {
        display: block;
    }
    #confirm-dialog Button {
        margin-right: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.export_mode = True
        self.selected_import_path: str | None = None
        self.export_pending_path: Path | None = None
        self.import_pending_path: Path | None = None

    def compose(self) -> ComposeResult:
        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model

        default_export = "No model loaded"
        if model:
            kdf_path = Path(model._parser.path)
            default_export = str(kdf_path.with_suffix(".xlsx"))

        saved_export = get_last_excel_export_path() or default_export
        saved_import = get_last_excel_import_path() or ""

        with Vertical(id="import-export-container"):
            yield Label("Import / Export Excel", classes="info-section")
            yield Static("─" * 25)

            with Horizontal(id="mode-toggle"):
                yield Button("Export", variant="primary", id="btn-mode-export")
                yield Button("Import", variant="default", id="btn-mode-import")

            with Vertical(id="export-panel"):
                yield Label("Export current model to Excel:")
                yield Static(saved_export, id="export-path-display", classes="path-display")

            with Vertical(id="import-panel", classes="hidden"):
                yield Label("Import Excel file:")
                yield TextArea(
                    text=saved_import,
                    id="import-path-input",
                    placeholder="Enter path to Excel file...",
                )
                with Horizontal(id="file-picker-buttons"):
                    yield Button("Browse", variant="default", id="btn-browse-import")
                    yield Button("Use Last", variant="default", id="btn-use-last-import")
                yield Static(
                    saved_import or "No file selected",
                    id="import-path-display",
                    classes="path-display",
                )

            with Horizontal(id="action-buttons"):
                yield Button("Execute", variant="primary", id="btn-execute")
                yield Button("Back", variant="default", id="btn-back")

            yield RichLog(id="results-log", wrap=True)

        yield Footer()

    @on(Button.Pressed, "#btn-mode-export")
    def set_export_mode(self) -> None:
        """Switch to export mode."""
        self.export_mode = True
        self.selected_import_path = None
        self.export_pending_path = None
        self.import_pending_path = None
        self.query_one("#btn-mode-export", Button).variant = "primary"
        self.query_one("#btn-mode-import", Button).variant = "default"
        self.query_one("#export-panel", Vertical).remove_class("hidden")
        self.query_one("#import-panel", Vertical).add_class("hidden")

        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model

        if model:
            kdf_path = Path(model._parser.path)
            default_export = str(kdf_path.with_suffix(".xlsx"))
            saved = get_last_excel_export_path() or default_export
            self.query_one("#export-path-display", Static).update(saved)

    @on(Button.Pressed, "#btn-mode-import")
    def set_import_mode(self) -> None:
        """Switch to import mode."""
        self.export_mode = False
        self.export_pending_path = None
        self.import_pending_path = None
        self.query_one("#btn-mode-import", Button).variant = "primary"
        self.query_one("#btn-mode-export", Button).variant = "default"
        self.query_one("#import-panel", Vertical).remove_class("hidden")
        self.query_one("#export-panel", Vertical).add_class("hidden")

        saved = get_last_excel_import_path()
        text_area = self.query_one("#import-path-input", TextArea)
        if saved:
            text_area.text = saved
            self.query_one("#import-path-display", Static).update(saved)
        else:
            text_area.text = ""
            self.query_one("#import-path-display", Static).update("No file selected")

    @on(Button.Pressed, "#btn-browse-import")
    def browse_import_file(self) -> None:
        """Open file browser for Excel file."""
        from pykorf.use_case.tui.screens.file_picker import FilePickerScreen

        # Create a custom file picker for .xlsx files
        class ExcelPickerScreen(FilePickerScreen):
            def load_file(self) -> None:
                path_input = self.query_one("#file-path-input", TextArea)
                error_label = self.query_one("#file-error", Label)
                raw_path = path_input.text.replace("\n", "").strip().strip('"').strip("'")

                if not raw_path:
                    error_label.update("Please enter a file path.")
                    return

                path = Path(raw_path)

                if not path.exists():
                    error_label.update(f"File not found: {path}")
                    return

                if path.suffix.lower() != ".xlsx":
                    error_label.update(
                        f"Invalid file type: {path.suffix}. Please select .xlsx file."
                    )
                    return

                # Pass path back to import/export screen
                self.app.pop_screen()
                import_screen = self.app.screen
                if isinstance(import_screen, ImportExportScreen):
                    text_area = import_screen.query_one("#import-path-input", TextArea)
                    text_area.text = str(path)
                    import_screen.selected_import_path = str(path)
                    import_screen.query_one("#import-path-display", Static).update(str(path))

        self.app.push_screen(ExcelPickerScreen())

    @on(Button.Pressed, "#btn-use-last-import")
    def use_last_import_path(self) -> None:
        """Load last used import path."""
        saved = get_last_excel_import_path()
        if saved:
            text_area = self.query_one("#import-path-input", TextArea)
            text_area.text = saved
            self.selected_import_path = saved
            self.query_one("#import-path-display", Static).update(saved)
        else:
            log_warning(
                self.query_one("#results-log", RichLog),
                "No previously used import path.",
            )

    @on(Button.Pressed, "#btn-execute")
    def execute(self) -> None:
        """Execute import or export based on current mode."""
        if self.export_mode:
            self._handle_export_request()
        else:
            self._handle_import_request()

    def _handle_export_request(self) -> None:
        """Handle export request with confirmation and overwrite check."""
        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)
        results = self.query_one("#results-log", RichLog)

        model = app.model
        if model is None:
            log_error(results, "No model loaded. Cannot export.")
            return

        # Always default to KDF folder, ignore saved path for export location
        kdf_path = Path(model._parser.path)
        export_path = kdf_path.with_suffix(".xlsx")

        # If we have a pending export confirmation, proceed with export
        if self.export_pending_path and self.export_pending_path == export_path:
            self.export_pending_path = None
            self._run_export(str(export_path))
            return

        self.export_pending_path = None

        # Check if file exists
        if export_path.exists():
            log_warning(results, f"⚠️  File already exists: {export_path.name}")
            log_warning(results, "Click Execute again to overwrite.")
            self.export_pending_path = export_path
            return

        # Show confirmation for new file
        log_info(results, f"Will export to: {export_path}")
        log_info(results, "Click Execute again to confirm export.")
        self.export_pending_path = export_path

    def _handle_import_request(self) -> None:
        """Handle import request with filename convention check."""
        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)
        results = self.query_one("#results-log", RichLog)

        # Get path from TextArea input
        text_area = self.query_one("#import-path-input", TextArea)
        import_path_str = text_area.text.strip()

        if not import_path_str:
            log_warning(results, "Please enter or browse to an Excel file.")
            return

        import_path = Path(import_path_str)

        if not import_path.exists():
            log_error(results, f"File not found: {import_path}")
            return

        if import_path.suffix.lower() != ".xlsx":
            log_error(
                results, f"Invalid file type: {import_path.suffix}. Please select .xlsx file."
            )
            return

        # Update selected path
        self.selected_import_path = str(import_path)
        self.query_one("#import-path-display", Static).update(str(import_path))

        # If we have a pending import confirmation (after warning), proceed
        if self.import_pending_path and self.import_pending_path == import_path:
            self.import_pending_path = None
            self._run_import(str(import_path))
            return

        self.import_pending_path = None

        # Check filename convention
        model = app.model
        if model:
            kdf_basename = Path(model._parser.path).stem
            import_basename = import_path.stem

            if kdf_basename != import_basename:
                log_warning(results, "⚠️  Filename mismatch:")
                log_warning(results, f"   Model: {kdf_basename}.kdf")
                log_warning(results, f"   Import: {import_path.name}")
                log_warning(results, "Click Execute again to proceed anyway.")
                self.import_pending_path = import_path
                return

        # Show confirmation for replacement
        log_warning(results, "⚠️  This will replace the current model. Continue?")
        log_warning(results, "Click Execute again to proceed.")
        self.import_pending_path = import_path

    @work(thread=True)
    def _run_export(self, path: str) -> None:
        """Export current model to Excel."""
        from pykorf.use_case.tui.app import UseCaseTUI

        results = self.query_one("#results-log", RichLog)
        app = self.app
        assert isinstance(app, UseCaseTUI)

        self.app.call_from_thread(results.clear)

        model = app.model
        if model is None:
            self.app.call_from_thread(lambda: log_error(results, "No model loaded. Cannot export."))
            return

        try:
            export_path = Path(path)

            self.app.call_from_thread(lambda: log_info(results, f"Exporting to: {export_path}"))

            model.io.to_excel(str(export_path), overwrite=True)

            set_last_excel_export_path(str(export_path))

            self.app.call_from_thread(lambda: log_success(results, "✅ Export successful!"))
            self.app.call_from_thread(lambda: log_info(results, f"Saved to: {export_path}"))
            self.app.call_from_thread(app.show_notification, f"✅ Exported: {export_path.name}")

        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Export failed: {e}"))

    @work(thread=True)
    def _run_import(self, path: str) -> None:
        """Import model from Excel file."""
        from pykorf.model.services.io import IOService
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.main_menu import MainMenuScreen

        results = self.query_one("#results-log", RichLog)
        app = self.app
        assert isinstance(app, UseCaseTUI)

        self.app.call_from_thread(results.clear)

        try:
            self.app.call_from_thread(lambda: log_info(results, f"Importing from: {path}"))

            dfs = IOService.excel_to_dataframes(path)
            model = IOService.model_from_dataframes(dfs)

            set_last_excel_import_path(path)

            app.model = model

            import_path = Path(path)
            model._parser.path = import_path.with_suffix(".kdf")

            self.app.call_from_thread(lambda: log_success(results, "✅ Import successful!"))
            self.app.call_from_thread(lambda: log_info(results, f"Loaded: {import_path.name}"))
            self.app.call_from_thread(app.update_file_header, str(model._parser.path))
            self.app.call_from_thread(app.show_notification, f"✅ Imported: {import_path.name}")

            def _go_back():
                self.app.push_screen(MainMenuScreen())

            self.app.call_from_thread(_go_back)

        except Exception as exc:
            self.app.call_from_thread(lambda e=exc: log_error(results, f"Import failed: {e}"))

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        """Return to main menu."""
        from pykorf.use_case.tui.screens.main_menu import MainMenuScreen

        self.export_pending_path = None
        self.import_pending_path = None
        self.app.push_screen(MainMenuScreen())
