"""Global Settings screen for applying bulk modifications to the model."""

from __future__ import annotations

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Label, RichLog, Static

from pykorf.log import get_log_file
from pykorf.use_case.tui.logging import (
    get_log_entries,
    log_error,
    log_info,
    log_success,
    log_warning,
)


class GlobalSettingsScreen(Screen):
    """Screen for applying global settings to the model."""

    BINDINGS = [("escape", "action_go_back", "Back")]

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

    CSS = """
    GlobalSettingsScreen {
        align: center middle;
    }
    #global-settings-box {
        width: 80;
        height: auto;
        max-height: 50;
        border: round $accent;
        padding: 1 2;
    }
    #global-settings-box Label {
        margin-bottom: 1;
    }
    #settings-list {
        height: auto;
        margin: 1 0;
    }
    #settings-list Checkbox {
        margin-bottom: 1;
    }
    #settings-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    #settings-buttons Button {
        margin: 0 1;
    }
    #settings-results {
        height: 12;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #settings-results RichLog {
        overflow-x: hidden;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="global-settings-box"):
            yield Label("Apply Global Settings")
            yield Static("Select settings to apply:")
            yield Static("---")

            # Load settings and their saved selections
            from pykorf.use_case.config import get_global_settings_selected
            from pykorf.use_case.global_settings import get_global_settings

            settings = get_global_settings()
            saved_selections = get_global_settings_selected()

            with Vertical(id="settings-list"):
                for setting in settings:
                    # Default to selected if saved selection contains this setting ID
                    is_selected = setting.id in saved_selections
                    yield Checkbox(
                        setting.name,
                        value=is_selected,
                        id=f"checkbox-{setting.id}",
                    )
                    # Add description as a smaller static text
                    yield Static(
                        f"  {setting.description}",
                        id=f"desc-{setting.id}",
                        classes="setting-desc",
                    )

            yield Static("---")
            with Horizontal(id="settings-buttons"):
                yield Button("Select All", variant="default", id="btn-select-all")
                yield Button("Apply Selected", variant="primary", id="btn-apply")
                yield Button("Back", variant="default", id="btn-back")
            yield RichLog(id="settings-results", wrap=True)
        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-select-all")
    def select_all(self) -> None:
        """Select all checkboxes."""
        from pykorf.use_case.global_settings import get_global_settings

        settings = get_global_settings()
        for setting in settings:
            checkbox = self.query_one(f"#checkbox-{setting.id}", Checkbox)
            checkbox.value = True

    @on(Button.Pressed, "#btn-apply")
    def apply_settings(self) -> None:
        self._run_apply()

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Save selections when checkboxes are changed."""
        from pykorf.use_case.config import set_global_settings_selected
        from pykorf.use_case.global_settings import get_global_settings

        # Collect all selected setting IDs
        settings = get_global_settings()
        selected_ids = []
        for setting in settings:
            checkbox = self.query_one(f"#checkbox-{setting.id}", Checkbox)
            if checkbox.value:
                selected_ids.append(setting.id)

        # Save to config
        set_global_settings_selected(selected_ids)

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

        # Clear logs
        self.app.call_from_thread(results.clear)
        self._clear_logs()

        # Get selected settings
        settings = get_global_settings()
        selected_ids = []
        for setting in settings:
            checkbox = self.query_one(f"#checkbox-{setting.id}", Checkbox)
            if checkbox.value:
                selected_ids.append(setting.id)

        if not selected_ids:
            self.app.call_from_thread(
                lambda: self._log(
                    results,
                    "No settings selected. Please select at least one setting.",
                    "error",
                )
            )
            return

        # Save selections to config
        set_global_settings_selected(selected_ids)

        # Get the model
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

        # Show preview of what will be changed
        self.app.call_from_thread(
            lambda: self._log(results, "Applying Global Settings:")
        )
        for setting_id in selected_ids:
            setting = next(s for s in settings if s.id == setting_id)
            self.app.call_from_thread(
                lambda s=setting: self._log(results, f"  - {s.name}: {s.description}")
            )
        self.app.call_from_thread(lambda: self._log(results, ""))

        try:
            # Apply the settings
            apply_results = apply_global_settings(model, selected_ids, save=False)

            # Check for errors from apply_global_settings
            errors = apply_results.get("_errors", [])
            for error in errors:
                self.app.call_from_thread(
                    lambda e=error: self._log(results, f"ERROR: {e}", "error")
                )

            # Fetch WARNING/ERROR logs from use_case.global_settings and display them
            log_file = get_log_file()
            if log_file:
                entries = get_log_entries(
                    log_file,
                    levels={"WARNING", "ERROR", "CRITICAL"},
                    logger_filter="pykorf.use_case.global_settings",
                )
                if entries:
                    self.app.call_from_thread(
                        lambda: log_warning(
                            results,
                            "Warnings/Errors during global settings processing:",
                        )
                    )
                    for _ts, _name, level, message in entries:
                        if level == "WARNING":
                            self.app.call_from_thread(
                                lambda m=message: log_warning(results, f"  ⚠ {m}")
                            )
                        else:
                            self.app.call_from_thread(
                                lambda m=message: log_error(results, f"  ✗ {m}")
                            )

            # Display results
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
                        lambda c=count: self._log(
                            results, f"    - (showing first 10 of {c})"
                        )
                    )
                    for pipe_name in pipes[:10]:
                        self.app.call_from_thread(
                            lambda n=pipe_name: self._log(results, f"    - {n}")
                        )

            self.app.call_from_thread(
                lambda: self._log(
                    results, f"\nTotal: {total_affected} pipe(s) modified", "success"
                )
            )

            # Check if errors occurred
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
                    lambda: self._log(
                        results, "Model updated in memory. Save to persist changes."
                    )
                )

            # Push save confirm screen (user can view logs there)
            self.app.call_from_thread(self.app.push_screen, SaveConfirmScreen(model))

        except Exception as exc:
            self.app.call_from_thread(
                lambda e=exc: self._log(
                    results, f"Error applying settings: {e}", "error"
                )
            )
