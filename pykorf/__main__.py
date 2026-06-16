"""Command-line entry point for pyKorf.

Supports both ``python -m pykorf`` and the ``pykorf`` console script.
"""

from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def get_version() -> str:
    """Get the package version dynamically."""
    try:
        return version("pykorf")
    except PackageNotFoundError:
        return "dev"


def show_splash() -> None:
    """Display pyKorf splash screen with branding."""
    console.clear()
    console.print()
    console.print()

    pkg_version = get_version()

    content = Text(justify="center")
    content.append("pyKorf", style="bold cyan")
    content.append(f"  v{pkg_version}\n", style="bold white")
    content.append("\n")
    content.append("Enterprise Hydraulic Modeling Toolkit\n", style="cyan")
    content.append("\n")
    content.append("KDF editor  ·  PMS/HMB automation  ·  Excel reporting", style="dim")

    console.print(
        Panel(
            content,
            border_style="cyan",
            padding=(1, 6),
            width=70,
        ),
        justify="center",
    )
    console.print()


def main():
    """Launch the pyKorf web application."""
    parser = argparse.ArgumentParser(
        prog="pykorf",
        description="Enterprise Python toolkit for KORF hydraulic model files.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (default: on for development)",
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Run in user mode with reduced terminal noise",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the web UI server (default: 8000)",
    )
    args = parser.parse_args()

    debug = not args.no_debug

    show_splash()

    from pykorf.app import run_server

    run_server(port=args.port, debug=debug)


if __name__ == "__main__":
    main()
