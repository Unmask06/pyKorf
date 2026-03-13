"""Configuration menu screen for managing PMS and Stream data files."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, RichLog, Static

from pykorf.use_case.tui.logging import log_error, log_info, log_success, log_warning


class ConfigMenuScreen(Screen):
    """Screen for managing configuration files."""

    CSS_PATH = []

    CSS = """
    ConfigMenuScreen {
        align: center middle;
    }
    #config-container {
        width: 100%;
        height: 100%;
    }
    #config-form {
        padding: 0 1;
    }
    #config-form Label {
        margin-bottom: 0;
        height: 1;
    }
    #config-form Input {
        margin-bottom: 0;
        height: 3;
    }
    #config-form Button {
        width: 100%;
        margin-bottom: 0;
        height: 3;
        padding: 0 1;
    }
    #config-results {
        width: 100%;
        height: 1fr;
        border: round $surface;
        margin-top: 1;
        overflow-x: hidden;
    }
    #config-results RichLog {
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
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="config-container"), Horizontal():
            with Vertical(id="left-panel"), Vertical(id="config-form"):
                yield Label("Configuration Management", classes="info-section")
                yield Static("─" * 30)

                yield Label("Import PMS from Excel:")
                yield Input(
                    placeholder="Path to PMS Excel file",
                    id="pms-excel-input",
                )
                yield Input(
                    placeholder="Output filename (default: pms.json)",
                    id="pms-output-input",
                )
                yield Button(
                    "Import PMS from Excel",
                    variant="primary",
                    id="btn-import-pms",
                )

                yield Static("---")

                yield Label("Import Stream Data from Excel:")
                yield Input(
                    placeholder="Path to Stream Data Excel file",
                    id="stream-excel-input",
                )
                yield Input(
                    placeholder="Output filename (default: stream_data.json)",
                    id="stream-output-input",
                )
                yield Button(
                    "Import Stream Data from Excel",
                    variant="primary",
                    id="btn-import-stream",
                )

                yield Static("---")
                yield Button(
                    "List Config Files",
                    variant="default",
                    id="btn-list-configs",
                )
                yield RichLog(id="config-results", wrap=True)

                with Horizontal(id="config-footer"):
                    yield Button("Back", variant="default", id="btn-back")

            with Vertical(id="right-panel"):
                with Vertical(classes="info-section"):
                    yield Label("PMS Config")
                    yield Static("─" * 15)
                    yield Static("PMS defines pipe")
                    yield Static("specifications.")
                    yield Static("")
                    yield Static("Stored in:")
                    yield Static("  %APPDATA%\\pyKorf\\data\\")
                    yield Static("  pms.json")

                with Vertical(classes="info-section"):
                    yield Label("Stream Config")
                    yield Static("─" * 15)
                    yield Static("Stream data contains")
                    yield Static("fluid properties.")
                    yield Static("")
                    yield Static("Stored in:")
                    yield Static("  %APPDATA%\\pyKorf\\data\\")
                    yield Static("  stream_data.json")

                with Vertical(classes="info-section"):
                    yield Label("Config File")
                    yield Static("─" * 15)
                    yield Static("User preferences")
                    yield Static("(last file path, etc.)")
                    yield Static("")
                    yield Static("Stored in:")
                    yield Static("  %APPDATA%\\pyKorf\\")
                    yield Static("  config.json")
        yield Footer()

    def on_mount(self) -> None:
        """Load last interaction data when screen mounts."""
        from pykorf.use_case.config import get_last_interaction

        results_log = self.query_one("#config-results", RichLog)

        last_interaction = get_last_interaction()
        if last_interaction.get("screen") == "config_menu":
            data = last_interaction.get("data", {})
            pms_excel_path = data.get("pms_excel_path", "")
            if pms_excel_path:
                self.query_one("#pms-excel-input", Input).value = pms_excel_path
            pms_output = data.get("pms_output", "")
            if pms_output:
                self.query_one("#pms-output-input", Input).value = pms_output
            stream_excel_path = data.get("stream_excel_path", "")
            if stream_excel_path:
                self.query_one("#stream-excel-input", Input).value = stream_excel_path
            stream_output = data.get("stream_output", "")
            if stream_output:
                self.query_one("#stream-output-input", Input).value = stream_output

    @on(Button.Pressed, "#btn-import-pms")
    def import_pms(self) -> None:
        """Import PMS data from Excel file."""
        from pykorf.use_case.config import (
            get_last_interaction,
            import_pms_from_excel,
            set_last_interaction,
        )

        results = self.query_one("#config-results", RichLog)
        results.clear()

        excel_path = self.query_one("#pms-excel-input", Input).value.strip().strip('"').strip("'")
        output_name = self.query_one("#pms-output-input", Input).value.strip().strip('"').strip("'")

        if not excel_path:
            log_error(results, "Please enter the Excel file path.")
            return

        if not output_name:
            output_name = "pms.json"

        try:
            path = import_pms_from_excel(excel_path, output_name)
            log_success(results, "Imported PMS from Excel:")
            log_info(results, f"  {path}")
            # Merge with existing data, only update non-empty values
            last_interaction = get_last_interaction()
            data = (
                last_interaction.get("data", {})
                if last_interaction.get("screen") == "config_menu"
                else {}
            )
            data["pms_excel_path"] = excel_path
            data["pms_output"] = output_name
            set_last_interaction("config_menu", data)
        except Exception as exc:
            log_error(results, f"Error importing PMS: {exc}")

    @on(Button.Pressed, "#btn-import-stream")
    def import_stream(self) -> None:
        """Import stream data from Excel file."""
        from pykorf.use_case.config import (
            get_last_interaction,
            import_stream_from_excel,
            set_last_interaction,
        )

        results = self.query_one("#config-results", RichLog)
        results.clear()

        excel_path = (
            self.query_one("#stream-excel-input", Input).value.strip().strip('"').strip("'")
        )
        output_name = (
            self.query_one("#stream-output-input", Input).value.strip().strip('"').strip("'")
        )

        if not excel_path:
            log_error(results, "Please enter the Excel file path.")
            return

        if not output_name:
            output_name = "stream_data.json"

        try:
            path = import_stream_from_excel(excel_path, output_name)
            log_success(results, "Imported Stream Data from Excel:")
            log_info(results, f"  {path}")
            # Merge with existing data, only update non-empty values
            last_interaction = get_last_interaction()
            data = (
                last_interaction.get("data", {})
                if last_interaction.get("screen") == "config_menu"
                else {}
            )
            data["stream_excel_path"] = excel_path
            data["stream_output"] = output_name
            set_last_interaction("config_menu", data)
        except Exception as exc:
            log_error(results, f"Error importing Stream Data: {exc}")

    @on(Button.Pressed, "#btn-list-configs")
    def list_configs(self) -> None:
        """List all configuration files."""
        from pykorf.use_case.config import ensure_config_dir, list_config_files

        results = self.query_one("#config-results", RichLog)
        results.clear()

        try:
            config_dir = ensure_config_dir()
            files = list_config_files()

            log_info(results, f"Config Directory: {config_dir}")

            if files["pms"]:
                log_info(results, "PMS Files:")
                for f in files["pms"]:
                    log_info(results, f"  - {f}")

            if files["streams"]:
                log_info(results, "Stream Files:")
                for f in files["streams"]:
                    log_info(results, f"  - {f}")

            if files["other"]:
                log_info(results, "Other Files:")
                for f in files["other"]:
                    log_info(results, f"  - {f}")

            if not any(files.values()):
                log_warning(results, "No configuration files found.")

        except Exception as exc:
            log_error(results, f"Error listing configs: {exc}")
