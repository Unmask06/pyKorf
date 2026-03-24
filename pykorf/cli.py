"""Command-line entry point for pyKorf TUI."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from time import sleep

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from pykorf.update import check_for_update, install_update

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


def show_loading(message: str, duration: float = 0.5) -> None:
    """Show a brief loading animation.

    Args:
        message: Message to display during loading
        duration: Duration in seconds
    """
    with console.status(f"[dim]{message}[/dim]", spinner="dots"):
        sleep(duration)


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


def show_update_prompt(update_info: dict) -> None:
    """Display update available prompt and handle user response.

    Args:
        update_info: Dict with 'latest_version', 'release_url', and 'zipball_url' keys.
    """
    latest_version = update_info["latest_version"]
    release_url = update_info.get("release_url", "")
    zipball_url = update_info.get("zipball_url", "")
    release_notes = update_info.get("release_notes", "")

    body = f"A newer version of pyKorf is available: [bold cyan]v{latest_version}[/bold cyan]\n"
    if release_notes:
        body += "\n[bold]What's new:[/bold]\n"
        body += f"[dim]{release_notes}[/dim]\n"
    if release_url:
        body += f"\n[dim]{release_url}[/dim]"
    body += "\n\nInstall now? [Y/n]"

    console.print(
        Panel(body, title="📦 Update Available", border_style="green", padding=(0, 1)),
        justify="center",
    )

    response = console.input().strip().lower()

    if response not in ("", "y", "yes"):
        return

    console.print()

    if not zipball_url:
        console.print("[yellow]No download URL available — please update manually.[/yellow]")
        console.print()
        console.print("[dim]Press Enter to continue...[/dim]")
        console.input()
        return

    success = False
    message = ""

    with console.status("[dim]Downloading update...[/dim]", spinner="dots"):
        success, message = install_update(zipball_url)

    if success:
        console.print(
            Panel(
                f"[green]{message}[/green]",
                title="✅ Update Installed",
                border_style="green",
                padding=(0, 1),
            ),
            justify="center",
        )
    else:
        console.print(
            Panel(
                f"[red]{message}[/red]",
                title="❌ Update Failed",
                border_style="red",
                padding=(0, 1),
            ),
            justify="center",
        )

    console.print()
    console.print("[dim]Press Enter to continue...[/dim]")
    console.input()


def main():
    """Launch the pyKorf TUI application."""
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
        help="Enable debug mode (DEBUG log level, saves to {kdf-name}-debug.log)",
    )
    args = parser.parse_args()

    show_splash()

    if args.trial:
        if check_trial_expired():
            show_expired_message()
            return
        days_left = (TRIAL_START_DATE + timedelta(days=TRIAL_DURATION_DAYS) - datetime.now()).days
        show_trial_info(max(0, days_left))

    pkg_version = get_version()
    if pkg_version != "dev":
        update_info = check_for_update(pkg_version)
        if update_info:
            show_update_prompt(update_info)

    show_loading("Initializing...", 0.8)

    from pykorf.use_case.tui import run_tui

    run_tui(debug=args.debug)


if __name__ == "__main__":
    main()
