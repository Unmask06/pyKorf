"""Command-line entry point for pyKorf.

Supports both ``python -m pykorf`` and the ``pykorf`` console script.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from importlib.metadata import PackageNotFoundError, version

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

TRIAL_START_DATE = datetime(2026, 3, 15)
TRIAL_DURATION_DAYS = 7
DEVELOPER_CONTACT = "Prasanna Palanivel"

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
            Align.center(content),
            border_style="cyan",
            padding=(1, 6),
            width=70,
        ),
        justify="center",
    )
    console.print()


def check_trial_expired() -> bool:
    """Check if the trial period has expired.

    Returns:
        True if trial has expired, False otherwise.
    """
    expiry_date = TRIAL_START_DATE + timedelta(days=TRIAL_DURATION_DAYS)
    return datetime.now() > expiry_date


def show_expired_message() -> None:
    """Display trial expired message and exit."""
    console.clear()
    console.print()
    console.print()
    console.print()

    console.print(
        Panel(
            f"[red bold]Trial Period Expired[/red bold]\n\n"
            f"The [yellow]{TRIAL_DURATION_DAYS}-day[/yellow] trial has ended.\n\n"
            f"To continue using pyKorf, please contact:\n"
            f"[bold cyan]{DEVELOPER_CONTACT}[/bold cyan]",
            title="[red]⚠ Access Expired[/red]",
            border_style="red",
            padding=(1, 2),
        ),
        justify="center",
    )
    console.print()


def show_trial_info(days_left: int) -> None:
    """Display trial period information.

    Args:
        days_left: Number of days remaining in trial
    """
    if days_left <= 3:
        style = "red bold"
        urgency = "⚠"
    elif days_left <= 7:
        style = "yellow"
        urgency = "i"
    else:
        style = "green"
        urgency = "✓"

    console.print(
        Panel(
            f"[{style}]Trial Mode: {days_left} days remaining[{style}]",
            title=f"{urgency} Trial Status",
            border_style="yellow" if days_left <= 7 else "green",
            padding=(0, 1),
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
        "--trial",
        action="store_true",
        help="Run in trial mode (time-limited access)",
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

    if args.trial:
        if check_trial_expired():
            show_expired_message()
            return
        days_left = (TRIAL_START_DATE + timedelta(days=TRIAL_DURATION_DAYS) - datetime.now()).days
        show_trial_info(max(0, days_left))

    from pykorf.app import run_server

    run_server(port=args.port, debug=debug)


if __name__ == "__main__":
    main()
