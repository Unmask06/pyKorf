"""Configuration menu screen for managing PMS and Stream data files."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Static


class ConfigMenuScreen(Screen):
    """Screen for managing configuration files."""

    BINDINGS = [("escape", "go_back", "Back")]

    CSS = """
    ConfigMenuScreen {
        align: center middle;
    }
    #config-box {
        width: 80;
        height: auto;
        max-height: 50;
        border: round $accent;
        padding: 1 2;
    }
    #config-box Label {
        margin-bottom: 1;
    }
    #config-box Input {
        margin-bottom: 1;
    }
    #config-buttons {
        height: auto;
        margin: 1 0;
    }
    #config-buttons Button {
        width: 100%;
        margin-bottom: 1;
    }
    #config-results {
        height: 10;
        border: round $surface;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="config-box"):
            yield Label("[bold]Configuration Management[/bold]")
            yield Static("---")
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
        yield Footer()

    def on_mount(self) -> None:
        """Load last interaction data when screen mounts."""
        from pykorf.use_case.config import get_last_interaction

        last_interaction = get_last_interaction()
        if last_interaction.get("screen") == "config_menu":
            data = last_interaction.get("data", {})
            if "pms_excel_path" in data:
                self.query_one("#pms-excel-input", Input).value = data["pms_excel_path"]
            if "pms_output" in data:
                self.query_one("#pms-output-input", Input).value = data["pms_output"]
            if "stream_excel_path" in data:
                self.query_one("#stream-excel-input", Input).value = data["stream_excel_path"]
            if "stream_output" in data:
                self.query_one("#stream-output-input", Input).value = data["stream_output"]

    def action_go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-back")
    def go_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-import-pms")
    def import_pms(self) -> None:
        """Import PMS data from Excel file."""
        from pykorf.use_case.config import import_pms_from_excel, set_last_interaction

        results = self.query_one("#config-results", RichLog)
        results.clear()

        excel_path = self.query_one("#pms-excel-input", Input).value.strip().strip('"').strip("'")
        output_name = self.query_one("#pms-output-input", Input).value.strip().strip('"').strip("'")

        if not excel_path:
            results.write("[red]Please enter the Excel file path.[/red]")
            return

        if not output_name:
            output_name = "pms.json"

        try:
            path = import_pms_from_excel(excel_path, output_name)
            results.write("[green]Imported PMS from Excel:[/green]")
            results.write(f"  {path}")
            set_last_interaction(
                "config_menu", {"pms_excel_path": excel_path, "pms_output": output_name}
            )
        except Exception as exc:
            results.write(f"[red]Error importing PMS: {exc}[/red]")

    @on(Button.Pressed, "#btn-import-stream")
    def import_stream(self) -> None:
        """Import stream data from Excel file."""
        from pykorf.use_case.config import import_stream_from_excel, set_last_interaction

        results = self.query_one("#config-results", RichLog)
        results.clear()

        excel_path = (
            self.query_one("#stream-excel-input", Input).value.strip().strip('"').strip("'")
        )
        output_name = (
            self.query_one("#stream-output-input", Input).value.strip().strip('"').strip("'")
        )

        if not excel_path:
            results.write("[red]Please enter the Excel file path.[/red]")
            return

        if not output_name:
            output_name = "stream_data.json"

        try:
            path = import_stream_from_excel(excel_path, output_name)
            results.write("[green]Imported Stream Data from Excel:[/green]")
            results.write(f"  {path}")
            set_last_interaction(
                "config_menu", {"stream_excel_path": excel_path, "stream_output": output_name}
            )
        except Exception as exc:
            results.write(f"[red]Error importing Stream Data: {exc}[/red]")

    @on(Button.Pressed, "#btn-list-configs")
    def list_configs(self) -> None:
        """List all configuration files."""
        from pykorf.use_case.config import ensure_config_dir, list_config_files

        results = self.query_one("#config-results", RichLog)
        results.clear()

        try:
            config_dir = ensure_config_dir()
            files = list_config_files()

            results.write(f"[bold]Config Directory:[/bold] {config_dir}")
            results.write("")

            if files["pms"]:
                results.write("[bold]PMS Files:[/bold]")
                for f in files["pms"]:
                    results.write(f"  - {f}")
                results.write("")

            if files["streams"]:
                results.write("[bold]Stream Files:[/bold]")
                for f in files["streams"]:
                    results.write(f"  - {f}")
                results.write("")

            if files["other"]:
                results.write("[bold]Other Files:[/bold]")
                for f in files["other"]:
                    results.write(f"  - {f}")

            if not any(files.values()):
                results.write("[dim]No configuration files found.[/dim]")

        except Exception as exc:
            results.write(f"[red]Error listing configs: {exc}[/red]")
