"""Main menu screen with use case options."""

from __future__ import annotations

import datetime
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from pykorf import __version__


def _check_excel_needs_reimport() -> tuple[bool, bool]:
    """Check whether the PMS or Stream Excel sources have been modified since last import.

    Compares each Excel file's modification time against the stored last-imported
    timestamp.  Returns a pair of booleans: (pms_stale, stream_stale).
    """
    from pykorf.use_case.preferences import (
        get_last_interaction,
        get_pms_excel_last_imported,
        get_pms_excel_path,
        get_stream_excel_last_imported,
    )

    def _is_stale(excel_path_str: str | None, last_imported_str: str | None) -> bool:
        if not excel_path_str or not last_imported_str:
            return False
        try:
            p = Path(excel_path_str)
            if not p.is_file():
                return False
            file_mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
            last_imported = datetime.datetime.fromisoformat(last_imported_str)
            return file_mtime > last_imported
        except (OSError, ValueError):
            return False

    pms_stale = _is_stale(get_pms_excel_path(), get_pms_excel_last_imported())

    stream_path = get_last_interaction().get("stream_excel_path")
    stream_stale = _is_stale(stream_path, get_stream_excel_last_imported())

    return pms_stale, stream_stale


class MainMenuScreen(Screen):
    """Central menu showing use-case operations."""

    BINDINGS = [
        ("1", "bulk_copy", "Bulk Copy Fluids"),
        ("2", "apply_pms", "Apply PMS"),
        ("3", "apply_hmb", "Apply HMB"),
        ("4", "model_info", "Model Info"),
        ("e", "generate_report", "Generate Report"),
        ("g", "global_settings", "Global Settings"),
        ("c", "config_menu", "Config Menu"),
        ("l", "load_file", "Load File"),
        ("x", "import_export", "Import/Export Excel"),
    ]

    CSS_PATH = []

    CSS = """
    MainMenuScreen {
        align: center middle;
    }
    #menu-container {
        width: 100%;
        height: 100%;
    }
    #file-label {
        width: 100%;
        height: auto;
        color: $accent;
        text-style: bold;
        padding: 0 1;
    }
    #file-path-label {
        width: 100%;
        height: auto;
        color: $text-muted;
        padding: 0 1;
    }
    #modified-indicator {
        width: 100%;
        height: auto;
        color: $warning;
        text-style: bold;
        padding: 0 1;
    }
    #main-content {
        width: 100%;
        height: 1fr;
    }
    #left-panel {
        width: 70%;
        height: 100%;
        overflow-y: auto;
    }
    #right-panel {
        width: 30%;
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
    }
    #menu-buttons {
        width: 100%;
        height: auto;
        padding: 1 1;
    }
    .menu-item {
        width: 100%;
        height: 3;
        margin-bottom: 1;
    }
    .menu-item Button {
        width: 20;
        height: 3;
        padding: 0 1;
        margin-right: 2;
    }
    .menu-item Label {
        width: 1fr;
        content-align: left middle;
        color: $text-muted;
        padding: 0 1;
    }
    #menu-footer {
        width: 100%;
        height: auto;
        padding: 1 0 0 0;
        dock: bottom;
    }
    #menu-footer Button {
        width: 14;
        height: 3;
        margin-right: 1;
    }
    #right-panel-content {
        padding: 0 1;
    }
    .stat-row {
        height: 1;
        margin-bottom: 0;
    }
    .stat-label {
        color: $text-muted;
        width: 12;
    }
    .stat-value {
        color: $text;
        text-style: bold;
    }
    .quick-action-btn {
        width: 100%;
        margin-bottom: 0;
        height: 3;
    }
    .side-panel-section {
        margin-bottom: 1;
    }
    .side-panel-section Label {
        text-style: bold;
        color: $accent;
    }
    .side-panel-section Static {
        color: $text-muted;
        text-style: dim;
    }
    #validation-success {
        color: $success;
        text-style: bold;
        margin-top: 1;
    }
    .menu-section-header {
        width: 100%;
        height: 1;
        color: $accent;
        text-style: bold;
        padding: 0 1;
        margin-top: 1;
    }
    .menu-section-divider {
        width: 100%;
        height: 1;
        color: $accent-darken-2;
        margin-bottom: 0;
    }
    """

    def compose(self) -> ComposeResult:
        app = self.app
        from pykorf.use_case.tui.app import UseCaseTUI

        assert isinstance(app, UseCaseTUI)
        model = app.model

        file_name = "No file loaded"
        pipe_count = 0
        feed_count = 0
        product_count = 0
        pump_count = 0
        modified_indicator = ""
        validation_issues: list[str] = []
        if model is not None:
            from pathlib import Path

            file_name = Path(model._parser.path).name
            from pykorf.use_case.tui.screens import real_elements

            pipe_count = len(real_elements(model.pipes))
            feed_count = len(real_elements(model.feeds))
            product_count = len(real_elements(model.products))
            pump_count = len(real_elements(model.pumps))
            if model.is_file_modified():
                modified_indicator = "⚠ File modified externally"

            validation_issues = model.validate()

        pms_stale, stream_stale = _check_excel_needs_reimport()
        config_btn_label = "⚙ Config Menu"
        config_btn_variant = "default"
        config_description = "Manage PMS and stream data files"
        if pms_stale or stream_stale:
            config_btn_label = "⚙ Config Menu ▲"
            config_btn_variant = "warning"
            stale_names = []
            if pms_stale:
                stale_names.append("PMS")
            if stream_stale:
                stale_names.append("Stream")
            config_description = (
                f"▲ {'/'.join(stale_names)} Excel updated — re-import recommended"
            )

        with Vertical(id="menu-container"):
            yield Label(f"pyKorf Use Case Tool V{__version__}", id="file-label")
            yield Label(f"📄 {file_name}", id="file-path-label")
            if modified_indicator:
                yield Label(modified_indicator, id="modified-indicator")

            with Horizontal(id="main-content"):
                with Vertical(id="left-panel"):
                    with Vertical(id="menu-buttons"):
                        yield Label("▸ Model Operations", classes="menu-section-header")
                        yield Static("─" * 35, classes="menu-section-divider")
                        with Horizontal(classes="menu-item"):
                            yield Button("⧉ Bulk Copy", variant="primary", id="btn-bulk-copy")
                            yield Label("Copy fluids between elements")
                        with Horizontal(classes="menu-item"):
                            yield Button("▲ Apply PMS", variant="primary", id="btn-apply-pms")
                            yield Label("Apply pipe material specifications")
                        with Horizontal(classes="menu-item"):
                            yield Button("⚖ Apply HMB", variant="primary", id="btn-apply-hmb")
                            yield Label("Apply heat and mass balance data")
                        with Horizontal(classes="menu-item"):
                            yield Button(
                                "⚙ Apply Global", variant="primary", id="btn-global-settings"
                            )
                            yield Label("Apply bulk modifications to all pipes")

                        yield Label("▸ Analysis & Reports", classes="menu-section-header")
                        yield Static("─" * 35, classes="menu-section-divider")
                        with Horizontal(classes="menu-item"):
                            yield Button("◎ Model Info", variant="primary", id="btn-model-info")
                            yield Label("View model statistics and validation")
                        with Horizontal(classes="menu-item"):
                            yield Button(
                                "★ Gen. Report", variant="success", id="btn-generate-report"
                            )
                            yield Label("Export results to Excel summary")

                        yield Label("▸ Configuration", classes="menu-section-header")
                        yield Static("─" * 35, classes="menu-section-divider")
                        with Horizontal(classes="menu-item"):
                            yield Button(
                                config_btn_label,
                                variant=config_btn_variant,
                                id="btn-config",
                            )
                            yield Label(config_description)
                        with Horizontal(classes="menu-item"):
                            yield Button(
                                "⇄ Import/Export", variant="primary", id="btn-import-export"
                            )
                            yield Label("Import/Export model to/from Excel")
                    with Horizontal(id="menu-footer"):
                        yield Button("Load File", variant="warning", id="btn-load-file")
                        yield Button("Quit", variant="error", id="btn-quit")

                with Vertical(id="right-panel"):
                    with Vertical(classes="side-panel-section"):
                        yield Label("Validation")
                        yield Static("─" * 20)
                        if validation_issues:
                            yield Label(
                                f"⚠ {len(validation_issues)} Issues Found",
                                id="validation-title",
                                classes="text-error",
                            )
                            yield Static("See Model Info for details")
                        else:
                            yield Label("✓ Model is valid", id="validation-success")

                    with Vertical(classes="side-panel-section"):
                        yield Label("Model Statistics")
                        yield Static("─" * 20)
                        yield self._stat_row("Pipes", pipe_count)
                        yield self._stat_row("Feeds", feed_count)
                        yield self._stat_row("Products", product_count)
                        yield self._stat_row("Pumps", pump_count)

                    with Vertical(classes="side-panel-section"):
                        yield Label("Quick Actions")
                        yield Static("─" * 20)
                        yield Button(
                            "Reload", variant="default", id="btn-reload", classes="quick-action-btn"
                        )
                        yield Button(
                            "Save", variant="default", id="btn-save", classes="quick-action-btn"
                        )
                        yield Button(
                            "Validate",
                            variant="default",
                            id="btn-validate",
                            classes="quick-action-btn",
                        )

                    with Vertical(classes="side-panel-section"):
                        yield Label("Tips")
                        yield Static("─" * 20)
                        yield Static("• Use semicolons for multi-case values")
                        yield Static("• Press Q to quit anytime")
                        yield Static("• Esc to go back")
        yield Footer()

    def _stat_row(self, label: str, value: int) -> Static:
        """Create a statistics row."""
        return Static(f"{label:<12}{value}", classes="stat-row")

    def on_mount(self) -> None:
        """Update bindings display."""
        self.set_interval(0.5, self._update_bindings)

    def _update_bindings(self) -> None:
        """Keep footer bindings updated."""
        pass

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

    @on(Button.Pressed, "#btn-global-settings")
    def action_global_settings(self) -> None:
        from pykorf.use_case.tui.screens.global_settings import GlobalSettingsScreen

        self.app.push_screen(GlobalSettingsScreen())

    @on(Button.Pressed, "#btn-config")
    def action_config_menu(self) -> None:
        from pykorf.use_case.tui.screens.config_menu import ConfigMenuScreen

        self.app.push_screen(ConfigMenuScreen())

    @on(Button.Pressed, "#btn-generate-report")
    def action_generate_report(self) -> None:
        """Switch to Generate Report screen."""
        from pykorf.use_case.tui.screens.generate_report import GenerateReportScreen

        self.app.push_screen(GenerateReportScreen())

    def action_import_export(self) -> None:
        """Switch to Import/Export Excel screen (keyboard binding)."""
        from pykorf.use_case.tui.screens.import_export import ImportExportScreen

        self.app.push_screen(ImportExportScreen())

    @on(Button.Pressed, "#btn-import-export")
    def action_import_export_button(self) -> None:
        """Switch to Import/Export Excel screen (button click)."""
        self.action_import_export()

    @on(Button.Pressed, "#btn-load-file")
    def action_load_file(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-reload")
    def action_reload_button(self) -> None:
        """Reload the current KDF file from disk."""
        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)
        app.action_reload_file()

    @on(Button.Pressed, "#btn-save")
    def action_save_button(self) -> None:
        """Save the current model."""
        from pykorf.use_case.tui.app import UseCaseTUI

        app = self.app
        assert isinstance(app, UseCaseTUI)
        model = app.model

        if model is None:
            return

        try:
            model.save()
            app.show_notification("File saved successfully")
        except Exception as exc:
            app.show_notification(f"Error saving file: {exc}")

    @on(Button.Pressed, "#btn-validate")
    def action_validate_button(self) -> None:
        """Show validation info."""
        from pykorf.use_case.tui.screens.model_info import ModelInfoScreen

        self.app.push_screen(ModelInfoScreen())

    @on(Button.Pressed, "#btn-quit")
    def action_quit_app(self) -> None:
        self.app.exit()
