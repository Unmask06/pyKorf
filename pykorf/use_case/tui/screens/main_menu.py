"""Main menu screen with use case options."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from pykorf import __version__


class MainMenuScreen(Screen):
    """Central menu showing use-case operations."""

    BINDINGS = [
        ("1", "bulk_copy", "Bulk Copy Fluids"),
        ("2", "apply_pms", "Apply PMS"),
        ("3", "apply_hmb", "Apply HMB"),
        ("4", "model_info", "Model Info"),
        ("g", "global_settings", "Global Settings"),
        ("c", "config_menu", "Config Menu"),
        ("l", "load_file", "Load File"),
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

        with Vertical(id="menu-container"):
            yield Label(f"pyKorf Use Case Tool V{__version__}", id="file-label")
            yield Label(f"📄 {file_name}", id="file-path-label")
            if modified_indicator:
                yield Label(modified_indicator, id="modified-indicator")

            with Horizontal(id="main-content"):
                with Vertical(id="left-panel"):
                    with Vertical(id="menu-buttons"):
                        with Horizontal(classes="menu-item"):
                            yield Button("Bulk Copy", variant="primary", id="btn-bulk-copy")
                            yield Label("Copy fluids between elements")
                        with Horizontal(classes="menu-item"):
                            yield Button("Apply PMS", variant="primary", id="btn-apply-pms")
                            yield Label("Apply pressure management system")
                        with Horizontal(classes="menu-item"):
                            yield Button("Apply HMB", variant="primary", id="btn-apply-hmb")
                            yield Label("Apply heat and mass balance")
                        with Horizontal(classes="menu-item"):
                            yield Button("Model Info", variant="primary", id="btn-model-info")
                            yield Label("View model statistics and validation")
                        with Horizontal(classes="menu-item"):
                            yield Button(
                                "Global Settings", variant="primary", id="btn-global-settings"
                            )
                            yield Label("Configure global parameters")
                        with Horizontal(classes="menu-item"):
                            yield Button("Config", variant="default", id="btn-config")
                            yield Label("Element configuration")
                    with Horizontal(id="menu-footer"):
                        yield Button("Load File", variant="warning", id="btn-load-file")
                        yield Button("Quit", variant="error", id="btn-quit")

                with Vertical(id="right-panel"):
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
