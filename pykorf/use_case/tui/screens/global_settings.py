"""Global Settings screen for applying bulk modifications to the model."""

from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Label, LoadingIndicator, RichLog, Static

from pykorf.log import get_log_file
from pykorf.use_case.tui.logging import (
    display_log_entries,
    log_error,
    log_info,
    log_success,
    reload_if_modified,
)


class GlobalSettingsScreen(Screen):
    """Screen for applying global settings to the model."""

    CSS_PATH = []

    def __init__(self):
        super().__init__()
        self.execution_logs: list[tuple[str, str]] = []
        self.has_errors = False

    def _log(self, results: RichLog, message: str, level: str = "info") -> None:
        """Log to both RichLog and persistent storage."""
        if level == "error":
            log_error(results, message)
            self.has_errors = True
        elif level == "success":
            log_success(results, message)
        else:
            log_info(results, message)

        self.execution_logs.append((level, message))

    def _clear_logs(self) -> None:
        """Clear persistent logs."""
        self.execution_logs.clear()
        self.has_errors = False

    def _get_selected_setting_ids(self) -> list[str]:
        from pykorf.use_case.global_settings import get_global_settings

        settings = get_global_settings()
        return [
            setting.id
            for setting in settings
            if self.query_one(f"#checkbox-{setting.id}", Checkbox).value
        ]

    CSS = """
    GlobalSettingsScreen {
        align: center middle;
    }
    #global-settings-container {
        width: 100%;
        height: 100%;
    }
    #main-content {
        width: 100%;
        height: 100%;
    }
    #left-panel {
        width: 70%;
        height: 100%;
    }
    #right-panel {
        width: 30%;
        height: 100%;
    }
    #settings-list {
        padding: 0 1;
        height: 1fr;
        overflow-y: auto;
    }
    #settings-list Checkbox {
        margin-bottom: 0;
        height: auto;
        min-height: 1;
    }
    .setting-desc {
        height: auto;
        color: $text-muted;
        text-style: dim;
        margin-bottom: 0;
        padding: 0 0 0 3;
    }
    #settings-buttons {
        height: auto;
        margin-top: 1;
        padding: 0 1;
    }
    #settings-buttons Button {
        margin-right: 1;
        height: 3;
        padding: 0 1;
    }
    #settings-results {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #settings-results RichLog {
        overflow-x: hidden;
    }
    #apply-loading {
        display: none;
        height: 1;
        margin-left: 1;
    }
    #apply-loading.active {
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
    """

    def compose(self) -> ComposeResult:
        from pykorf.use_case.config import get_global_settings_selected
        from pykorf.use_case.global_settings import get_global_settings

        settings = get_global_settings()
        saved_selections = get_global_settings_selected()

        with Vertical(id="global-settings-container"), Horizontal(id="main-content"):
            with Vertical(id="left-panel"):
                with Vertical(id="settings-list"):
                    yield Label("Apply Global Settings", classes="info-section")
                    yield Static("─" * 30)
                    for setting in settings:
                        is_selected = setting.id in saved_selections
                        yield Checkbox(
                            setting.name,
                            value=is_selected,
                            id=f"checkbox-{setting.id}",
                        )
                        yield Static(
                            f"  {setting.description}",
                            id=f"desc-{setting.id}",
                            classes="setting-desc",
                        )

                with Horizontal(id="settings-buttons"):
                    yield Button("Select All", variant="default", id="btn-select-all")
                    yield Button("Apply Selected", variant="primary", id="btn-apply")
                    yield LoadingIndicator(id="apply-loading")
                yield RichLog(id="settings-results", wrap=True)

            with Vertical(id="right-panel"):
                with Vertical(classes="info-section"):
                    yield Label("About")
                    yield Static("─" * 15)
                    yield Static("Global settings apply")
                    yield Static("bulk modifications to")
                    yield Static("all pipes in the model.")

                with Vertical(classes="info-section"):
                    yield Label("Common Settings")
                    yield Static("─" * 15)
                    yield Static("• Dummy Pipes & Junctions")
                    yield Static("• Friction drop design margin")
                    yield Static("• Bulk Rename Pipes")

                with Vertical(classes="info-section"):
                    yield Label("Tip")
                    yield Static("─" * 15)
                    yield Static("Select multiple settings")
                    yield Static("and apply together for")
                    yield Static("efficient updates.")
        yield Footer()

    @on(Button.Pressed, "#btn-select-all")
    def select_all(self) -> None:
        """Select all checkboxes."""
        from pykorf.use_case.global_settings import get_global_settings

        for setting in get_global_settings():
            self.query_one(f"#checkbox-{setting.id}", Checkbox).value = True

    @on(Button.Pressed, "#btn-apply")
    def apply_settings(self) -> None:
        self.query_one("#btn-apply", Button).disabled = True
        self.query_one("#apply-loading").add_class("active")
        self._run_apply()

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:
        from pykorf.use_case.config import set_global_settings_selected

        set_global_settings_selected(self._get_selected_setting_ids())

    @work(thread=True)
    def _run_apply(self) -> None:
        """Apply selected global settings in a background thread."""
        from pykorf.use_case.config import set_global_settings_selected
        from pykorf.use_case.global_settings import (
            apply_global_settings,
            get_global_settings,
        )
        from pykorf.use_case.tui.app import UseCaseTUI
        from pykorf.use_case.tui.screens.save_confirm import SaveConfirmScreen

        results = self.query_one("#settings-results", RichLog)
        try:
            self.app.call_from_thread(results.clear)
            self._clear_logs()

            settings = get_global_settings()
            selected_ids = self._get_selected_setting_ids()

            if not selected_ids:
                self.app.call_from_thread(
                    lambda: self._log(
                        results,
                        "No settings selected. Please select at least one setting.",
                        "error",
                    )
                )
                return

            set_global_settings_selected(selected_ids)

            app = self.app
            assert isinstance(app, UseCaseTUI)
            model = app.model
            if model is None:
                self.app.call_from_thread(
                    lambda: self._log(
                        results, "No model loaded. Please load a KDF file first.", "error"
                    )
                )
                return

            self.app.call_from_thread(lambda: self._log(results, "Applying Global Settings:"))
            for setting_id in selected_ids:
                setting = next(s for s in settings if s.id == setting_id)
                self.app.call_from_thread(
                    lambda s=setting: self._log(results, f"  - {s.name}: {s.description}")
                )
            self.app.call_from_thread(lambda: self._log(results, ""))

            reload_if_modified(model, self.app.call_from_thread, results)

            apply_results = apply_global_settings(model, selected_ids, save=False)
            errors = apply_results.get("_errors", [])
            for error in errors:
                self.app.call_from_thread(
                    lambda e=error: self._log(results, f"ERROR: {e}", "error")
                )

            display_log_entries(
                self.app.call_from_thread,
                results,
                get_log_file(),
                "pykorf.use_case.global_settings",
                "Warnings/Errors during global settings processing:",
            )

            total_affected = 0
            for setting_id, pipes in apply_results.items():
                if setting_id == "_errors":
                    continue
                setting = next(s for s in settings if s.id == setting_id)
                count = len(pipes)
                total_affected += count
                self.app.call_from_thread(
                    lambda s=setting, c=count: self._log(
                        results, f"{s.name}: {c} pipe(s) affected", "success"
                    )
                )
                if count > 0 and count <= 10:
                    for pipe_name in pipes:
                        self.app.call_from_thread(
                            lambda n=pipe_name: self._log(results, f"    - {n}")
                        )
                elif count > 10:
                    self.app.call_from_thread(
                        lambda c=count: self._log(results, f"    - (showing first 10 of {c})")
                    )
                    for pipe_name in pipes[:10]:
                        self.app.call_from_thread(
                            lambda n=pipe_name: self._log(results, f"    - {n}")
                        )

            self.app.call_from_thread(
                lambda: self._log(results, f"\nTotal: {total_affected} pipe(s) modified", "success")
            )

            if self.has_errors or errors:
                self.app.call_from_thread(
                    lambda: self._log(
                        results,
                        "\nWARNING: Some errors occurred. Review logs before saving.",
                        "error",
                    )
                )
            else:
                self.app.call_from_thread(
                    lambda: self._log(results, "Model updated in memory. Save to persist changes.")
                )

            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))

        except Exception as exc:
            self.app.call_from_thread(
                lambda e=exc: self._log(results, f"Error applying settings: {e}", "error")
            )
        finally:

            def _finish_settings():
                self.query_one("#btn-apply", Button).disabled = False
                self.query_one("#apply-loading").remove_class("active")

            self.app.call_from_thread(_finish_settings)
