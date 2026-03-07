"""
Command-line interface for pyKorf.

Provides commands for:
- Converting between formats
- Validating models
- Querying elements
- Exporting data
- Batch processing

Example:
    $ pykorf validate model.kdf
    $ pykorf convert model.kdf output.json --format json
    $ pykorf query model.kdf --type PIPE --where "diameter_inch > 6"
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pykorf.exceptions import KorfError

try:
    import click
    from rich.console import Console
    from rich.table import Table

    HAS_CLI_DEPS = True
except ImportError:
    HAS_CLI_DEPS = False

    # Create dummy classes for type checking
    class click:  # type: ignore
        class Context:
            pass

        @staticmethod
        def group(*args, **kwargs):
            return lambda f: f

        @staticmethod
        def command(*args, **kwargs):
            return lambda f: f

        @staticmethod
        def argument(*args, **kwargs):
            return lambda f: f

        @staticmethod
        def option(*args, **kwargs):
            return lambda f: f

        @staticmethod
        def version_option(*args, **kwargs):
            return lambda f: f

        @staticmethod
        def pass_context(f):
            return f

        @staticmethod
        def Path(*args, **kwargs):
            return str

    class Console:  # type: ignore
        def print(self, *args, **kwargs):
            print(*args)

    class Table:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def add_column(self, *args, **kwargs):
            pass

        def add_row(self, *args, **kwargs):
            pass


console = Console()


def ensure_deps() -> None:
    """Ensure CLI dependencies are available."""
    if not HAS_CLI_DEPS:
        console.print(
            "[red]CLI dependencies not installed. Install with: pip install pykorf[cli][/red]"
        )
        sys.exit(1)


if HAS_CLI_DEPS:

    @click.group()
    @click.version_option(version="0.2.0", prog_name="pykorf")
    @click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
    @click.pass_context
    def cli(ctx: click.Context, verbose: bool) -> None:
        """pyKorf - Python toolkit for KORF hydraulic models."""
        ensure_deps()
        ctx.ensure_object(dict)
        ctx.obj["verbose"] = verbose

    @cli.command()
    @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
    @click.option(
        "--output", "-o", type=click.Path(path_type=Path), help="Output file (default: stdout)"
    )
    @click.option(
        "--format", "fmt", type=click.Choice(["json", "yaml"]), default="json", help="Output format"
    )
    @click.option("--no-results", is_flag=True, help="Exclude calculated results")
    @click.pass_context
    def convert(
        ctx: click.Context,
        input_file: Path,
        output: Path | None,
        fmt: str,
        no_results: bool,
    ) -> None:
        """Convert a KDF file to JSON or YAML."""
        from pykorf import Model
        from pykorf.model.services.io import IOService
        from pykorf.types import ExportOptions

        try:
            model = Model(input_file)

            options = ExportOptions(
                include_results=not no_results,
                include_geometry=True,
                include_connectivity=True,
            )

            if output is None:
                output = input_file.with_suffix(f".{fmt}")

            with console.status(f"[bold green]Converting to {fmt.upper()}..."):
                if fmt == "json":
                    IOService(model=model).export_to_json(output, options=options)
                else:
                    IOService(model=model).export_to_yaml(output, options=options)

            console.print(f"[green]✓[/green] Converted to {output}")

            # Show summary
            table = Table(title="Model Summary")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")

            summary = model.summary()
            for key, value in summary.items():
                table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)

        except KorfError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    @cli.command()
    @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
    @click.option("--strict", is_flag=True, help="Enable strict validation mode")
    @click.pass_context
    def validate(ctx: click.Context, input_file: Path, strict: bool) -> None:
        """Validate a KDF file."""
        from pykorf import Model

        try:
            with console.status("[bold green]Loading model..."):
                model = Model(input_file)

            with console.status("[bold green]Validating..."):
                issues = model.validate()

            if not issues:
                console.print("[green]✓[/green] Model is valid")
            else:
                error_count = sum(1 for i in issues if "error" in i.lower())
                warning_count = len(issues) - error_count

                console.print(
                    f"[yellow]Found {len(issues)} issue(s): "
                    f"{error_count} error(s), {warning_count} warning(s)[/yellow]"
                )

                table = Table(title="Validation Issues")
                table.add_column("#", style="dim", width=4)
                table.add_column("Issue", style="yellow")

                for i, issue in enumerate(issues[:20], 1):
                    prefix = (
                        "[red]ERROR[/red]" if "error" in issue.lower() else "[yellow]WARN[/yellow]"
                    )
                    table.add_row(str(i), f"{prefix} {issue}")

                if len(issues) > 20:
                    table.add_row("...", f"[dim]And {len(issues) - 20} more...[/dim]")

                console.print(table)

                if error_count > 0:
                    sys.exit(1)

        except KorfError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    @cli.command()
    @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
    @click.option("--type", "element_type", help="Filter by element type (e.g., PIPE, PUMP)")
    @click.option("--name", help="Filter by name pattern (glob)")
    @click.option("--limit", "-n", type=int, help="Limit number of results")
    @click.option("--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table")
    @click.pass_context
    def query(
        ctx: click.Context,
        input_file: Path,
        element_type: str | None,
        name: str | None,
        limit: int | None,
        fmt: str,
    ) -> None:
        """Query elements in a KDF file."""
        from pykorf import Model

        try:
            model = Model(input_file)

            # Build query using Model.get_elements()
            if element_type:
                results = model.get_elements(etype=element_type.upper())
            elif name:
                results = model.get_elements(name=name)
            else:
                results = model.elements

            if limit:
                results = results[:limit]

            if not results:
                console.print("[yellow]No elements found[/yellow]")
                return

            if fmt == "json":
                import json

                data = [{"name": e.name, "type": e.etype} for e in results]
                console.print(json.dumps(data, indent=2))

            elif fmt == "csv":
                console.print("name,type,index")
                for elem in results:
                    console.print(f"{elem.name},{elem.etype},{elem.index}")

            else:  # table
                table = Table(title=f"Query Results ({len(results)} elements)")
                table.add_column("Index", style="dim", width=6)
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Description", style="magenta")

                for elem in results:
                    desc = elem.description if hasattr(elem, "description") else ""
                    table.add_row(str(elem.index), elem.name, elem.etype, desc or "")

                console.print(table)

        except KorfError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    @cli.command()
    @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
    @click.argument("output_file", type=click.Path(path_type=Path))
    @click.option("--format", type=click.Choice(["excel", "json", "yaml", "csv"]), required=True)
    @click.option("--no-results", is_flag=True, help="Exclude calculated results")
    @click.pass_context
    def export(
        ctx: click.Context,
        input_file: Path,
        output_file: Path,
        format: str,
        no_results: bool,
    ) -> None:
        """Export model data to various formats."""
        from pykorf import Model
        from pykorf.model.services.io import IOService
        from pykorf.types import ExportOptions

        try:
            model = Model(input_file)

            options = ExportOptions(
                include_results=not no_results,
                include_geometry=True,
                include_connectivity=True,
            )

            with console.status(f"[bold green]Exporting to {format}..."):
                io_service = IOService(model=model)
                if format == "json":
                    io_service.export_to_json(output_file, options=options)
                elif format == "yaml":
                    io_service.export_to_yaml(output_file, options=options)
                elif format == "excel":
                    io_service.export_to_excel(output_file, include_results=not no_results)
                elif format == "csv":
                    io_service.export_to_csv(output_file.parent, include_results=not no_results)
                    output_file = output_file.parent / "pipes.csv"

            console.print(f"[green]✓[/green] Exported to {output_file}")

        except KorfError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    @cli.command()
    @click.pass_context
    def tui(ctx: click.Context) -> None:
        """Launch the interactive TUI for use case operations."""
        from pykorf.use_case.tui import run_tui

        run_tui()

    @cli.command()
    @click.argument("input_file", type=click.Path(exists=True, path_type=Path))
    @click.pass_context
    def summary(ctx: click.Context, input_file: Path) -> None:
        """Display a summary of the model."""
        from pykorf import Model

        try:
            model = Model(input_file)

            table = Table(title=f"Model Summary: {input_file.name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")

            summary_data = model.summary()
            for key, value in summary_data.items():
                display_key = key.replace("_", " ").replace("num ", "").title()
                table.add_row(display_key, str(value))

            console.print(table)

            # Element breakdown
            console.print("\n[bold]Element Breakdown:[/bold]")

            elem_table = Table()
            elem_table.add_column("Type", style="cyan")
            elem_table.add_column("Count", style="magenta", justify="right")

            for etype in ["PIPE", "PUMP", "VALVE", "FEED", "PROD", "VESSEL", "COMP", "HX"]:
                count = len([e for e in model.get_elements_by_type(etype)])
                if count > 0:
                    elem_table.add_row(etype, str(count))

            console.print(elem_table)

        except KorfError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    if not HAS_CLI_DEPS:
        print("Error: CLI dependencies not installed.")
        print("Install with: pip install pykorf[cli]")
        sys.exit(1)
    cli()


__all__ = ["main"]
